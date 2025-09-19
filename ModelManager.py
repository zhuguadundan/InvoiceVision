#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理器 - 处理AI模型的下载、检测和管理
"""

import os
import sys
import json
import shutil
from pathlib import Path
import tarfile
import tempfile
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

# 尝试懒加载 PyQt5（在无GUI环境下保持可导入）
try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTextEdit, QMessageBox, QFileDialog
    )
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    HAS_QT = True
except Exception:
    HAS_QT = False

class ModelManager:
    """模型管理器"""
    
    def __init__(self):
        self.models_dir = Path("models")
        self.required_models = [
            "PP-OCRv5_mobile_det",
            "PP-OCRv5_mobile_rec",
            "ch_ppocr_mobile_v2.0_cls"
        ]
        
    def get_models_directory(self):
        """获取模型目录路径"""
        # 尝试多个可能的路径
        possible_paths = [
            Path("models"),  # 当前目录
            Path(sys.executable).parent / "models",  # exe同级目录
            Path.home() / "InvoiceVision" / "models",  # 用户目录
            Path("C:/InvoiceVision/models"),  # 系统目录
        ]
        
        for path in possible_paths:
            if path.exists() and self.check_models_complete(path):
                return path
                
        return Path("models")  # 默认返回当前目录下的models
    
    def check_models_complete(self, models_dir=None):
        """检查模型文件是否完整"""
        if models_dir is None:
            models_dir = self.get_models_directory()
            
        if not models_dir.exists():
            return False
            
        for model_name in self.required_models:
            model_path = models_dir / model_name
            if not model_path.exists():
                return False
            
            # 检查模型文件夹是否为空
            if not any(model_path.iterdir()):
                return False
                
        return True
    
    def get_models_info(self):
        """获取模型信息"""
        models_dir = self.get_models_directory()
        info = {
            "models_dir": str(models_dir),
            "exists": models_dir.exists(),
            "complete": self.check_models_complete(models_dir),
            "models": {}
        }
        
        for model_name in self.required_models:
            model_path = models_dir / model_name
            model_info = {
                "path": str(model_path),
                "exists": model_path.exists(),
                "size": 0
            }
            
            if model_path.exists():
                try:
                    # 计算模型目录大小
                    total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                    model_info["size"] = total_size
                except:
                    model_info["size"] = 0
                    
            info["models"][model_name] = model_info
            
        return info
    
    def copy_models_from_source(self, source_path):
        """从源路径复制模型文件"""
        source_path = Path(source_path)
        target_path = self.get_models_directory()
        
        if not source_path.exists():
            raise FileNotFoundError(f"源模型目录不存在: {source_path}")
        
        # 创建目标目录
        target_path.mkdir(parents=True, exist_ok=True)
        
        # 复制每个模型目录
        for model_name in self.required_models:
            source_model = source_path / model_name
            target_model = target_path / model_name
            
            if source_model.exists():
                if target_model.exists():
                    shutil.rmtree(target_model)
                shutil.copytree(source_model, target_model)
            else:
                raise FileNotFoundError(f"源目录中缺少模型: {model_name}")

    # ========== 恢复并增强：直接下载模型功能 ==========
    def download_models(self):
        """下载轻量模型（PP-OCRv5 mobile det/rec + ch_ppocr_mobile_v2.0_cls）。

        返回:
            bool: 全部下载/就绪返回 True，任一失败返回 False
        """
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # 官方模型直链（以 inference 模型为准）；det 如 v5 不可用，则回退至 v4 mobile det
        candidates = {
            "PP-OCRv5_mobile_rec": [
                "https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv5_mobile_rec_infer.tar",
            ],
            "PP-OCRv5_mobile_det": [
                # 先尝试 v5 mobile det（若暂不可用，将回退 v4）
                "https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv5_mobile_det_infer.tar",
                "https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv4_mobile_det_infer.tar",
            ],
            "ch_ppocr_mobile_v2.0_cls": [
                "https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar",
            ],
        }

        def need_download(dir_name: str) -> bool:
            d = self.models_dir / dir_name
            return (not d.exists()) or (d.exists() and not any(d.iterdir()))

        def extract_tar_to(tar_path: Path, target_dir: Path) -> None:
            target_dir.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tar_path, 'r') as tar:
                tar.extractall(path=target_dir)
            # 若出现 *_infer 子目录，则将其中文件上移至目标目录根
            subdirs = [p for p in target_dir.iterdir() if p.is_dir()]
            if len(subdirs) == 1 and (subdirs[0].name.endswith('_infer') or subdirs[0].name.endswith('_inference')):
                inner = subdirs[0]
                for item in inner.iterdir():
                    shutil.move(str(item), str(target_dir / item.name))
                shutil.rmtree(inner, ignore_errors=True)

        def download_and_extract(url: str, target_dir: Path) -> bool:
            try:
                with urlopen(url, timeout=30) as resp:
                    if getattr(resp, 'status', 200) != 200:
                        return False
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.tar') as tmpf:
                        tmpf.write(resp.read())
                        tmp_path = Path(tmpf.name)
                extract_tar_to(tmp_path, target_dir)
                try:
                    tmp_path.unlink(missing_ok=True)  # Py3.8 兼容：若报错则忽略
                except Exception:
                    pass
                return True
            except (HTTPError, URLError):
                return False
            except Exception:
                return False

        overall_ok = True
        for dir_name, urls in candidates.items():
            if not need_download(dir_name):
                continue
            ok = False
            target = self.models_dir / dir_name
            for u in urls:
                if download_and_extract(u, target):
                    ok = True
                    break
            if not ok:
                overall_ok = False

        return overall_ok
    
    def check_models_status(self):
        """检查模型状态 - InvoiceVision兼容接口"""
        models_dir = self.get_models_directory()
        
        if not models_dir.exists():
            return "missing_all", "模型目录不存在"
            
        missing_models = []
        for model_name in self.required_models:
            model_path = models_dir / model_name
            if not model_path.exists() or not any(model_path.iterdir()):
                missing_models.append(model_name)
        
        if len(missing_models) == len(self.required_models):
            return "missing_all", "所有模型都缺失"
        elif missing_models:
            return "partial", f"部分模型缺失: {', '.join(missing_models)}"
        else:
            return "complete", "所有模型完整"


if HAS_QT:
class ModelSetupDialog(QDialog):
    """模型设置对话框 - 支持本地复制与直接下载"""
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.model_manager = ModelManager()
            self.init_ui()
            
        def init_ui(self):
            """初始化UI"""
            self.setWindowTitle("InvoiceVision - 模型配置")
            self.setFixedSize(500, 350)
            self.setModal(True)
            
            layout = QVBoxLayout()
            
            # 标题
            title_label = QLabel("AI模型配置")
            title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # 说明文字
            desc_label = QLabel(
                "InvoiceVision需要AI模型文件才能正常工作。\n"
                "请从现有位置复制模型文件到本地。"
            )
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
            
            # 模型状态信息
            self.status_text = QTextEdit()
            self.status_text.setMaximumHeight(150)
            self.status_text.setReadOnly(True)
            layout.addWidget(self.status_text)
            
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.copy_button = QPushButton("从本地复制模型")
        self.copy_button.clicked.connect(self.copy_models)
        button_layout.addWidget(self.copy_button)

        self.download_button = QPushButton("下载轻量模型")
        self.download_button.clicked.connect(self.download_models)
        button_layout.addWidget(self.download_button)

        layout.addLayout(button_layout)
            
            # 关闭按钮
            self.close_button = QPushButton("稍后配置")
            self.close_button.clicked.connect(self.reject)
            layout.addWidget(self.close_button)
            
            self.setLayout(layout)
            
            # 更新状态信息
            self.update_status()
            
        def update_status(self):
            """更新模型状态信息"""
            info = self.model_manager.get_models_info()
            
            status_text = f"模型目录: {info['models_dir']}\n"
            status_text += f"目录存在: {'是' if info['exists'] else '否'}\n"
            status_text += f"模型完整: {'是' if info['complete'] else '否'}\n\n"
            
            status_text += "必需的模型文件:\n"
            for model_name, model_info in info['models'].items():
                status = "✓" if model_info['exists'] else "✗"
                size_mb = model_info['size'] / 1024 / 1024 if model_info['size'] > 0 else 0
                status_text += f"{status} {model_name} ({size_mb:.1f} MB)\n"
                
            self.status_text.setPlainText(status_text)
            
            # 如果模型已完整，启用确定按钮
            if info['complete']:
                self.close_button.setText("确定")
                try:
                    self.close_button.clicked.disconnect()
                except Exception:
                    pass
                self.close_button.clicked.connect(self.accept)
        
        def copy_models(self):
            """从本地复制模型"""
            source_dir = QFileDialog.getExistingDirectory(
                self, 
                "选择包含模型文件的目录",
                "",
                QFileDialog.ShowDirsOnly
            )
            
            if not source_dir:
                return
                
            try:
                self.model_manager.copy_models_from_source(source_dir)
                QMessageBox.information(self, "成功", "模型文件复制完成！")
                self.update_status()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"复制模型文件失败:\n{str(e)}")

        def download_models(self):
            """直接下载轻量模型到 models/ 目录"""
            try:
                self.download_button.setEnabled(False)
                ok = self.model_manager.download_models()
                if ok:
                    QMessageBox.information(self, "成功", "模型下载完成！")
                else:
                    QMessageBox.warning(self, "部分失败", "部分模型下载失败，请稍后重试或改用本地复制。")
                self.update_status()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"下载模型失败:\n{str(e)}")
            finally:
                self.download_button.setEnabled(True)

    def check_and_setup_models():
        """检查并设置模型，返回是否设置成功"""
        manager = ModelManager()
        
        # 如果模型已完整，直接返回True
        if manager.check_models_complete():
            return True
        
        # 否则显示配置对话框
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        dialog = ModelSetupDialog()
        result = dialog.exec_()
        
        # 再次检查模型是否完整
        return result == QDialog.Accepted and manager.check_models_complete()
else:
    # 无 GUI 环境下的降级实现
    def check_and_setup_models():
        return False


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 测试模型管理器
    manager = ModelManager()
    info = manager.get_models_info()
    print("模型信息:", json.dumps(info, indent=2, ensure_ascii=False))
    
    # 测试对话框
    dialog = ModelSetupDialog()
    dialog.show()
    
    sys.exit(app.exec_())
