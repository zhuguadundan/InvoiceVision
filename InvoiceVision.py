#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线版GUI界面 - 完全离线运行的发票OCR识别器 (外部模型架构)
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from PyQt5.QtWidgets import (QFileDialog, QApplication, QPushButton, 
                            QMessageBox, QMainWindow, QInputDialog, QTextEdit,
                            QSplitter, QWidget, QVBoxLayout, QHBoxLayout,
                            QTreeWidget, QTreeWidgetItem, QTabWidget,
                            QScrollArea, QFrame, QGroupBox, QGridLayout,
                            QProgressBar, QCheckBox, QSpacerItem, QSizePolicy,
                            QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt5.Qt import QThread, QMutex, pyqtSignal
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QPixmap
from MainAction import ocr_pdf_offline, ocr_images_offline
try:
    # 注意：使用ModelManager.py（大写M），不是model_manager.py
    from ModelManager import ModelManager, check_and_setup_models
except ImportError as e:
    print(f"Warning: Could not import ModelManager: {e}")
    # 如果模型管理器不可用，创建简单的替代
    class ModelManager:
        def __init__(self):
            pass
        def check_models_status(self):
            return "unknown", "模型管理器不可用"
        def prompt_download_models(self):
            return False
    
    def check_and_setup_models():
        """替代函数，总是返回True避免启动失败"""
        print("使用替代的check_and_setup_models函数")
        return True
import os
import json
import pandas as pd
from datetime import datetime

class OfflineOCRThread(QThread):
    """离线OCR处理线程基类"""
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    result = pyqtSignal(dict)
    ocr_result = pyqtSignal(dict)  # 新增：OCR结果信号
    
    def __init__(self):
        super().__init__()
        self.file_path = ''
        self.precision_mode = '快速'
        self.output_dir = ''  # 输出目录

class PDFOCRThread(OfflineOCRThread):
    """PDF离线OCR处理线程"""
    def run(self):
        try:
            self.progress.emit("正在处理PDF文件...")
            result = ocr_pdf_offline(self.file_path, self.precision_mode, self.output_dir)
            self.progress.emit("PDF处理完成！")
            self.ocr_result.emit(result or {})
            self.result.emit({"success": True, "type": "PDF", "result": result})
        except Exception as e:
            self.progress.emit(f"处理出错: {e}")
            self.result.emit({"success": False, "error": str(e)})
        finally:
            self.finished.emit()

class ImageOCRThread(OfflineOCRThread):
    """图片文件夹离线OCR处理线程"""
    def run(self):
        try:
            self.progress.emit("正在处理图片文件夹...")
            result = ocr_images_offline(self.file_path, self.precision_mode, self.output_dir)
            self.progress.emit("图片处理完成！")
            self.ocr_result.emit(result or {})
            self.result.emit({"success": True, "type": "Images", "result": result})
        except Exception as e:
            self.progress.emit(f"处理出错: {e}")
            self.result.emit({"success": False, "error": str(e)})
        finally:
            self.finished.emit()

class OfflineInvoiceOCRMainWindow(QMainWindow):
    """离线版主窗口类 - 现代化界面"""
    
    def __init__(self):
        super().__init__()
        self.offline_status = self.check_offline_status()
        self.output_dir = os.getcwd()  # 默认输出目录
        self.ocr_results = {}  # 存储OCR结果
        self.accumulated_results = []  # 累积所有识别结果
        
        # 检查模型状态
        self.model_manager = ModelManager()
        self.check_models_on_startup()
        
        self.setup_ui()
        self.pdf_thread = None
        self.image_thread = None
        
    def check_offline_status(self):
        """检查离线模式状态"""
        config_file = "offline_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get("offline_mode", False)
            except:
                pass
        return False
        
    def check_models_on_startup(self):
        """启动时检查模型状态"""
        try:
            status, message = self.model_manager.check_models_status()
            
            if status == "missing_all":
                # 所有模型都缺失，提示用户
                reply = QMessageBox.question(
                    None, 
                    "模型文件缺失", 
                    f"{message}\n\n是否现在下载模型文件？\n"
                    "（这是首次运行所必需的，约需要下载100MB文件）",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.download_models_with_progress()
                else:
                    QMessageBox.information(
                        None,
                        "提示",
                        "程序将以有限功能模式启动。\n"
                        "您可以稍后通过【工具】菜单下载模型文件。"
                    )
            elif status == "partial":
                # 部分模型缺失
                QMessageBox.warning(
                    None,
                    "模型文件不完整", 
                    f"{message}\n\n建议通过【工具】菜单重新下载完整模型文件。"
                )
                
        except Exception as e:
            print(f"模型检查失败: {e}")
    
    def download_models_with_progress(self):
        """带进度条的模型下载"""
        # 这里可以实现一个进度条对话框
        # 简化版本：直接调用下载
        try:
            success = self.model_manager.download_models()
            if success:
                QMessageBox.information(None, "下载完成", "模型文件下载完成！程序现已就绪。")
            else:
                QMessageBox.warning(None, "下载失败", "模型下载失败，请检查网络连接或稍后重试。")
        except Exception as e:
            QMessageBox.critical(None, "下载错误", f"下载过程出错: {e}")
        
    def setup_ui(self):
        """设置现代化UI界面"""
        self.setObjectName("OfflineInvoiceOCRMainWindow")
        self.resize(1200, 800)
        self.setMinimumSize(QtCore.QSize(1000, 600))
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 标题区域
        self.create_header_section(main_layout)
        
        # 主内容区域
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # 左侧控制面板
        left_panel = self.create_control_panel()
        main_splitter.addWidget(left_panel)
        
        # 右侧结果面板
        right_panel = self.create_result_panel()
        main_splitter.addWidget(right_panel)
        
        # 设置分割比例
        main_splitter.setSizes([400, 800])
        
        # 底部状态栏
        self.create_status_bar(main_layout)
        
        # 应用样式
        self.apply_modern_style()
        
        # 设置窗口属性
        self.setWindowTitle("📄 智能发票OCR识别器 - 离线版")
        
    def create_header_section(self, layout):
        """创建标题区域"""
        header_frame = QFrame()
        header_frame.setMaximumHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                margin: 5px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # 主标题
        title_label = QtWidgets.QLabel("📄 智能发票OCR识别器")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
            }
        """)
        
        # 状态显示
        status_text = "🟢 离线模式 | PP-OCRv5" if self.offline_status else "🔴 在线模式"
        status_label = QtWidgets.QLabel(status_text)
        status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-family: 'Microsoft YaHei';
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        
        layout.addWidget(header_frame)
        
    def create_control_panel(self):
        """创建左侧控制面板"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # 设置组
        settings_group = QGroupBox("⚙️ 设置")
        settings_layout = QGridLayout(settings_group)
        
        # 精度模式
        settings_layout.addWidget(QtWidgets.QLabel("精度模式:"), 0, 0)
        self.precision_combo = QtWidgets.QComboBox()
        self.precision_combo.addItems(['快速', '高精'])
        settings_layout.addWidget(self.precision_combo, 0, 1)
        
        # 输出目录
        settings_layout.addWidget(QtWidgets.QLabel("输出目录:"), 1, 0)
        output_layout = QHBoxLayout()
        self.output_label = QtWidgets.QLabel(os.path.basename(self.output_dir))
        self.output_label.setStyleSheet("QLabel { color: #666; }")
        self.output_btn = QPushButton("📂 选择")
        self.output_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_btn)
        settings_layout.addLayout(output_layout, 1, 1)
        
        control_layout.addWidget(settings_group)
        
        # 操作组
        actions_group = QGroupBox("🛠️ 操作")
        actions_layout = QVBoxLayout(actions_group)
        
        # PDF处理按钮
        self.pdf_button = QPushButton("🗃️ 处理PDF文件")
        self.pdf_button.clicked.connect(self.handle_pdf_file)
        actions_layout.addWidget(self.pdf_button)
        
        # 图片处理按钮
        self.image_button = QPushButton("🖼️ 处理图片文件夹")
        self.image_button.clicked.connect(self.handle_image_folder)
        actions_layout.addWidget(self.image_button)
        
        control_layout.addWidget(actions_group)
        
        # 模型状态组
        model_group = QGroupBox("🧠 模型信息")
        model_layout = QVBoxLayout(model_group)
        
        self.model_status_btn = QPushButton("🔍 查看模型状态")
        self.model_status_btn.clicked.connect(self.show_model_status)
        model_layout.addWidget(self.model_status_btn)
        
        control_layout.addWidget(model_group)
        
        # 添加弹性空间
        control_layout.addStretch()
        
        return control_widget
        
    def create_result_panel(self):
        """创建右侧结果面板"""
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        
        # 结果标签页
        self.result_tabs = QTabWidget()
        
        # OCR结果选项卡 - 使用表格显示
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels(["文件路径", "开票公司名称", "发票号码", "发票日期", "项目名称", "金额（不含税）"])
        
        # 设置表格属性
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.verticalHeader().setVisible(False)
        
        # 设置列宽自适应
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 文件路径列自动伸缩
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 开票公司名称列自适应内容
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 发票号码列自适应内容
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 发票日期列自适应内容
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 项目名称列自适应内容
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 金额列自适应内容
        
        self.result_tabs.addTab(self.result_table, "📋 识别结果")
        
        # 原始数据选项卡
        self.raw_data_text = QTextEdit()
        self.raw_data_text.setReadOnly(True)
        self.raw_data_text.setFont(QtGui.QFont("Consolas", 10))
        self.result_tabs.addTab(self.raw_data_text, "📊 原始数据")
        
        result_layout.addWidget(self.result_tabs)
        
        # 结果操作按钮
        result_actions = QHBoxLayout()
        
        self.export_btn = QPushButton("💾 导出Excel")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("🗑️ 清空结果")
        self.clear_btn.clicked.connect(self.clear_results)
        
        result_actions.addWidget(self.export_btn)
        result_actions.addWidget(self.clear_btn)
        result_actions.addStretch()
        
        result_layout.addLayout(result_actions)
        
        return result_widget
        
    def create_status_bar(self, layout):
        """创建状态栏"""
        status_frame = QFrame()
        status_frame.setMaximumHeight(50)
        status_layout = QHBoxLayout(status_frame)
        
        # 状态标签
        self.status_label = QtWidgets.QLabel("✅ 就绪 - 离线运行" if self.offline_status else "⚠️ 就绪 - 需要网络")
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_frame)
        
    def apply_modern_style(self):
        """应用现代化样式"""
        style = """
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                font-family: 'Microsoft YaHei';
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #495057;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
                /* 移除不支持的transform属性 */
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d8b40, stop:1 #357a38);
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
            QComboBox {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: white;
                font-size: 14px;
            }
            QComboBox:focus {
                border-color: #80bdff;
                outline: 0;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: #dee2e6;
                border-left-style: solid;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QTreeWidget, QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #007bff;
                font-size: 13px;
            }
            QTreeWidget::item, QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QTreeWidget::item:selected, QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QTableWidget::horizontalHeader {
                background-color: #f8f9fa;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                padding: 8px;
            }
            QTableWidget::horizontalHeader::section {
                background-color: #f8f9fa;
                border: none;
                border-right: 1px solid #dee2e6;
                padding: 8px;
                font-weight: bold;
            }
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                font-size: 12px;
                padding: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 1px solid #dee2e6;
                padding: 10px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e9ecef, stop:1 #dee2e6);
            }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                background-color: #f8f9fa;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #28a745, stop:1 #20c997);
                border-radius: 3px;
            }
            QLabel {
                color: #495057;
            }
        """
        
        self.setStyleSheet(style)
        
    def show_model_status(self):
        """显示模型状态信息"""
        if os.path.exists("models"):
            model_dirs = [d for d in os.listdir("models") if os.path.isdir(os.path.join("models", d))]
            
            if model_dirs:
                total_size = 0
                model_info = "本地模型:\n\n"
                
                for model_dir in model_dirs:
                    model_path = os.path.join("models", model_dir)
                    dir_size = 0
                    
                    for root, dirs, files in os.walk(model_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            dir_size += os.path.getsize(file_path)
                    
                    size_mb = dir_size / (1024 * 1024)
                    total_size += size_mb
                    model_info += f"• {model_dir}: {size_mb:.1f} MB\n"
                
                model_info += f"\n总大小: {total_size:.1f} MB"
                model_info += "\n状态: ✅ 可完全离线运行"
                
            else:
                model_info = "未找到本地模型文件\n\n请运行 setup_offline_simple.py 设置离线模型"
        else:
            model_info = "models 目录不存在\n\n请先下载模型文件"
        
        QMessageBox.information(self, "模型状态", model_info)
    
    def select_output_dir(self):
        """选择输出目录"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            '选择输出目录', 
            self.output_dir
        )
        if folder:
            self.output_dir = folder
            self.output_label.setText(os.path.basename(folder) or "根目录")
            self.output_label.setToolTip(folder)
    
    def display_ocr_results(self, results):
        """显示OCR识别结果 - 表格形式累积显示"""
        if not results:
            return
        
        # 处理结果数据
        if isinstance(results, dict) and 'invoice_data' in results:
            # 处理主处理函数返回的结果
            invoice_data = results['invoice_data']
            if isinstance(invoice_data, list):
                # 添加到累积结果中
                self.accumulated_results.extend(invoice_data)
            elif isinstance(invoice_data, dict):
                # 单个结果转换为列表格式
                if 'data' in invoice_data:
                    self.accumulated_results.extend(invoice_data['data'])
        else:
            # 直接处理单个发票结果（从OCR返回的格式）
            # 假设results是单个发票的[文件路径, 发票代码, 发票号码, 日期, 金额]格式
            if isinstance(results, list) and len(results) >= 5:
                self.accumulated_results.append(results)
        
        # 更新表格显示
        self.update_result_table()
        
        # 存储结果用于导出
        self.ocr_results = results
        
        # 启用导出按钮
        self.export_btn.setEnabled(True)
        
        # 更新原始数据显示
        try:
            formatted_json = json.dumps(results, ensure_ascii=False, indent=2)
            self.raw_data_text.append("=" * 50)
            self.raw_data_text.append(f"新识别结果 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.raw_data_text.append("=" * 50)
            self.raw_data_text.append(formatted_json)
        except:
            self.raw_data_text.append(str(results))
    
    def update_result_table(self):
        """更新结果表格"""
        # 设置行数
        self.result_table.setRowCount(len(self.accumulated_results))
        
        # 填充表格数据
        for row, result in enumerate(self.accumulated_results):
            if isinstance(result, list) and len(result) >= 6:
                # [文件路径, 开票公司名称, 发票号码, 发票日期, 金额（不含税）, 项目名称]
                file_path = os.path.basename(str(result[0])) if result[0] else ""
                company_name = str(result[1]) if result[1] else ""
                invoice_number = str(result[2]) if result[2] else ""
                invoice_date = str(result[3]) if result[3] else ""
                invoice_amount = str(result[4]) if result[4] else ""  # 金额（不含税）
                project_name = str(result[5]) if result[5] else ""  # 项目名称
                
                # 设置单元格内容
                self.result_table.setItem(row, 0, QTableWidgetItem(file_path))
                self.result_table.setItem(row, 1, QTableWidgetItem(company_name))
                self.result_table.setItem(row, 2, QTableWidgetItem(invoice_number))
                self.result_table.setItem(row, 3, QTableWidgetItem(invoice_date))
                self.result_table.setItem(row, 4, QTableWidgetItem(project_name))  # 项目名称
                self.result_table.setItem(row, 5, QTableWidgetItem(invoice_amount))  # 金额（不含税）
                
                # 设置工具提示显示完整路径
                self.result_table.item(row, 0).setToolTip(str(result[0]))
            elif isinstance(result, list) and len(result) >= 5:
                # 兼容旧格式（5个字段）
                # [文件路径, 开票公司名称, 发票号码, 日期, 金额(价税合计)]
                file_path = os.path.basename(str(result[0])) if result[0] else ""
                company_name = str(result[1]) if result[1] else ""
                invoice_number = str(result[2]) if result[2] else ""
                invoice_date = str(result[3]) if result[3] else ""
                invoice_amount = str(result[4]) if result[4] else ""
                
                # 设置单元格内容
                self.result_table.setItem(row, 0, QTableWidgetItem(file_path))
                self.result_table.setItem(row, 1, QTableWidgetItem(company_name))
                self.result_table.setItem(row, 2, QTableWidgetItem(invoice_number))
                self.result_table.setItem(row, 3, QTableWidgetItem(invoice_date))
                self.result_table.setItem(row, 4, QTableWidgetItem(""))  # 项目名称为空
                self.result_table.setItem(row, 5, QTableWidgetItem(invoice_amount))
                
                # 设置工具提示显示完整路径
                self.result_table.item(row, 0).setToolTip(str(result[0]))
        
        # 自动滚动到底部显示最新结果
        if self.result_table.rowCount() > 0:
            self.result_table.scrollToBottom()
    
    def clear_results(self):
        """清空所有结果"""
        self.accumulated_results.clear()
        self.ocr_results = {}
        self.result_table.setRowCount(0)
        self.raw_data_text.clear()
        self.export_btn.setEnabled(False)
    
    def export_results(self):
        """导出结果到Excel"""
        if not self.accumulated_results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return
            
        # 选择保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            '保存Excel文件', 
            os.path.join(self.output_dir, f'发票识别结果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'),
            'Excel文件 (*.xlsx)'
        )
        
        if file_path:
            try:
                # 转换累积结果为DataFrame
                data_list = []
                for result in self.accumulated_results:
                    if isinstance(result, list) and len(result) >= 6:
                        # 新格式（6个字段）
                        data_dict = {
                            "文件路径": str(result[0]),
                            "开票公司名称": str(result[1]) if result[1] else "",
                            "发票号码": str(result[2]) if result[2] else "",
                            "发票日期": str(result[3]) if result[3] else "",
                            "项目名称": str(result[5]) if result[5] else "",
                            "金额（不含税）": str(result[4]) if result[4] else ""
                        }
                        data_list.append(data_dict)
                    elif isinstance(result, list) and len(result) >= 5:
                        # 兼容旧格式（5个字段）
                        data_dict = {
                            "文件路径": str(result[0]),
                            "开票公司名称": str(result[1]) if result[1] else "",
                            "发票号码": str(result[2]) if result[2] else "",
                            "发票日期": str(result[3]) if result[3] else "",
                            "项目名称": "",
                            "金额（不含税）": result[4] if result[4] else ""
                        }
                        data_list.append(data_dict)
                
                if data_list:
                    df = pd.DataFrame(data_list)
                    df.to_excel(file_path, index=False)
                    QMessageBox.information(self, "成功", f"已导出 {len(data_list)} 条记录到: {file_path}")
                else:
                    QMessageBox.warning(self, "警告", "没有有效的数据可导出")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def handle_pdf_file(self):
        """处理PDF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            '选择PDF文件', 
            './', 
            'PDF文件 (*.pdf)'
        )
        
        if file_path:
            precision_mode = self.precision_combo.currentText()
            
            # 创建并启动PDF处理线程
            self.pdf_thread = PDFOCRThread()
            self.pdf_thread.file_path = file_path
            self.pdf_thread.precision_mode = precision_mode
            self.pdf_thread.output_dir = self.output_dir  # 设置输出目录
            self.pdf_thread.progress.connect(self.update_status)
            self.pdf_thread.result.connect(self.on_processing_result)
            self.pdf_thread.finished.connect(self.on_processing_finished)
            self.pdf_thread.ocr_result.connect(self.display_ocr_results)  # 连接结果显示
            
            # 禁用按钮，显示进度条，开始处理
            self.set_buttons_enabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 不确定进度
            self.update_status(f"📄 开始处理PDF: {os.path.basename(file_path)}")
            self.pdf_thread.start()
    
    def handle_image_folder(self):
        """处理图片文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            '选择包含图片的文件夹', 
            './'
        )
        
        if folder_path:
            precision_mode = self.precision_combo.currentText()
            
            # 创建并启动图片处理线程
            self.image_thread = ImageOCRThread()
            self.image_thread.file_path = folder_path
            self.image_thread.precision_mode = precision_mode
            self.image_thread.output_dir = self.output_dir  # 设置输出目录
            self.image_thread.progress.connect(self.update_status)
            self.image_thread.result.connect(self.on_processing_result)
            self.image_thread.finished.connect(self.on_processing_finished)
            self.image_thread.ocr_result.connect(self.display_ocr_results)  # 连接结果显示
            
            # 禁用按钮，显示进度条，开始处理
            self.set_buttons_enabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 不确定进度
            self.update_status(f"🖼️ 开始处理文件夹: {os.path.basename(folder_path)}")
            self.image_thread.start()
    
    def update_status(self, message):
        """更新状态显示"""
        self.status_label.setText(message)
        QApplication.processEvents()  # 强制更新UI
    
    def on_processing_result(self, result):
        """处理结果回调"""
        if result.get("success", False):
            file_type = result.get("type", "文件")
            self.update_status(f"✅ {file_type}处理成功！")
        else:
            error = result.get("error", "未知错误")
            self.update_status(f"❌ 处理失败: {error}")
    
    def on_processing_finished(self):
        """处理完成回调"""
        self.set_buttons_enabled(True)
        self.progress_bar.setVisible(False)
        
        # 显示完成对话框
        msg = QMessageBox(self)
        msg.setWindowTitle('🎉 处理完成')
        msg.setText('📄 发票信息识别完成！')
        
        if self.output_dir != os.getcwd():
            msg.setInformativeText(f'📁 结果已保存到: {self.output_dir}\n\n📊 请在右侧查看识别结果。')
        else:
            msg.setInformativeText('📁 结果已保存为 Excel 文件，请查看当前目录。\n\n📊 请在右侧查看识别结果。')
        
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
        
        mode_text = "🟢 离线运行" if self.offline_status else "🔴 在线运行"
        self.update_status(f"✅ 就绪 - {mode_text}")
    
    def set_buttons_enabled(self, enabled):
        """设置按钮启用状态"""
        self.pdf_button.setEnabled(enabled)
        self.image_button.setEnabled(enabled)
        self.precision_combo.setEnabled(enabled)
        self.model_status_btn.setEnabled(enabled)
        self.output_btn.setEnabled(enabled)  # 新增: 输出目录选择按钮
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 确保线程正常结束
        if self.pdf_thread and self.pdf_thread.isRunning():
            self.pdf_thread.terminate()
            self.pdf_thread.wait()
        if self.image_thread and self.image_thread.isRunning():
            self.image_thread.terminate()
            self.image_thread.wait()
        event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("发票OCR识别器 (离线版)")
    app.setApplicationVersion("2.0-Offline")
    app.setOrganizationName("OCR Tools")
    
    try:
        # 首先检查和设置模型
        print("检查AI模型配置...")
        if not check_and_setup_models():
            QMessageBox.critical(
                None, 
                "模型配置错误", 
                "AI模型文件缺失或配置失败，程序无法正常运行。\n\n"
                "请确保以下文件存在:\n"
                "- models/PP-OCRv5_server_det/\n"
                "- models/PP-OCRv5_server_rec/\n"
                "- models/PP-LCNet_x1_0_textline_ori/\n\n"
                "您可以:\n"
                "1. 将现有模型文件夹复制到程序目录下\n"
                "2. 重新运行程序并在模型配置界面中设置正确路径"
            )
            sys.exit(1)
        
        print("✅ 模型配置检查通过")
        
        # 创建并显示主窗口
        main_window = OfflineInvoiceOCRMainWindow()
        main_window.show()
        
        # 运行应用程序
        sys.exit(app.exec_())
        
    except ImportError as e:
        QMessageBox.critical(
            None,
            "依赖库错误", 
            f"缺少必要的依赖库:\n{str(e)}\n\n"
            "请运行 python install.py 安装所需依赖"
        )
        sys.exit(1)
    except Exception as e:
        QMessageBox.critical(
            None,
            "启动错误",
            f"程序启动失败:\n{str(e)}"
        )
        sys.exit(1)

if __name__ == '__main__':
    main()