#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线版GUI界面 - 完全离线运行的发票OCR识别器 (外部模型架构)
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from PyQt5.QtWidgets import (QFileDialog, QApplication, QPushButton,
                            QMessageBox, QMainWindow, QTextEdit,
                            QSplitter, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget,
                            QFrame, QGroupBox, QGridLayout,
                            QProgressBar,
                            QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt5.Qt import QThread, pyqtSignal
from PyQt5.QtCore import Qt
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

class PDFBatchOCRThread(OfflineOCRThread):
    """PDF 批量离线OCR处理线程"""
    def __init__(self):
        super().__init__()
        self.files = []  # PDF 文件列表
    
    def run(self):
        try:
            total = len(self.files)
            success_count = 0
            for idx, pdf_path in enumerate(self.files, start=1):
                self.progress.emit(f"正在处理PDF ({idx}/{total}): {os.path.basename(pdf_path)}")
                try:
                    result = ocr_pdf_offline(pdf_path, self.precision_mode, self.output_dir)
                    if result:
                        self.ocr_result.emit(result)
                        # 统计识别成功的条数（粗略按是否有数据判断）
                        if result.get('invoice_data'):
                            success_count += 1
                except Exception as e:
                    self.progress.emit(f"处理出错: {os.path.basename(pdf_path)} - {e}")
            
            self.progress.emit(f"PDF批量处理完成，共 {total} 个，成功 {success_count} 个")
            self.result.emit({"success": True, "type": "PDF批量", "result": {"total": total, "success": success_count}})
        except Exception as e:
            self.progress.emit(f"批量处理出错: {e}")
            self.result.emit({"success": False, "error": str(e)})
        finally:
            self.finished.emit()

class OfflineInvoiceOCRMainWindow(QMainWindow):
    """离线版主窗口类 - 现代化界面"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化调试日志
        self.log_debug("=== InvoiceVision 启动 ===", "INFO")
        
        self.offline_status = self.check_offline_status()
        self.log_debug(f"离线状态: {self.offline_status}", "INFO")
        
        self.output_dir = os.getcwd()  # 默认输出目录
        self.ocr_results = {}  # 存储OCR结果
        self.accumulated_results = []  # 累积所有识别结果
        
        # 检查模型状态
        self.model_manager = ModelManager()
        self.check_models_on_startup()
        
        # 🔥 关键修改：预初始化OCR引擎（在主线程中）
        self.log_debug("预初始化OCR引擎...", "INFO")
        self.global_ocr_initialized = self.pre_initialize_ocr()
        
        self.log_debug("设置用户界面...", "DEBUG")
        self.setup_ui()
        self.pdf_thread = None
        self.image_thread = None
        
        self.log_debug("初始化完成", "INFO")
        
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
        
    def pre_initialize_ocr(self):
        """预初始化OCR引擎 - 在主线程中完成，避免后续阻塞"""
        try:
            # 动态导入OCRInvoice模块
            import OCRInvoice
            
            # 获取当前精度模式
            precision_mode = '快速'  # 默认使用快速模式启动
            
            self.log_debug(f"开始预初始化OCR引擎，模式: {precision_mode}", "INFO")
            
            # 调用全局初始化方法
            success = OCRInvoice.OfflineOCRInvoice.global_initialize_ocr(precision_mode)
            
            if success:
                self.log_debug("[SUCCESS] OCR引擎预初始化成功", "INFO")
                return True
            else:
                self.log_debug("[ERROR] OCR引擎预初始化失败", "ERROR")
                # 显示警告但不阻止启动
                QMessageBox.warning(
                    None,
                    "OCR初始化警告", 
                    "OCR引擎预初始化失败，程序可能无法正常识别发票。\n\n"
                    "可能的原因：\n"
                    "1. 模型文件缺失或损坏\n"
                    "2. 依赖库不完整\n"
                    "3. 系统资源不足\n\n"
                    "您可以通过调试工具查看详细错误信息。"
                )
                return False
                
        except ImportError as e:
            self.log_debug(f"[ERROR] OCRInvoice模块导入失败: {e}", "ERROR")
            QMessageBox.critical(
                None,
                "模块导入错误",
                f"无法导入OCRInvoice模块:\n{str(e)}\n\n"
                "这可能是打包问题，请检查所有必要文件是否包含在内。"
            )
            return False
        except Exception as e:
            self.log_debug(f"[ERROR] OCR预初始化异常: {e}", "ERROR")
            import traceback
            self.log_debug(f"详细错误:\n{traceback.format_exc()}", "ERROR")
            return False
    
    def ensure_ocr_ready(self, precision_mode):
        """确保OCR引擎就绪，如有必要重新初始化"""
        try:
            import OCRInvoice
            
            # 检查当前状态
            status = OCRInvoice.OfflineOCRInvoice.get_initialization_status()
            self.log_debug(f"当前OCR状态: {status}", "DEBUG")
            
            if status == "ready":
                self.log_debug("OCR引擎已就绪", "DEBUG")
                return True
            elif status == "failed":
                self.log_debug("OCR引擎之前初始化失败，尝试重新初始化", "INFO")
            elif status == "pending":
                self.log_debug("OCR引擎未初始化，现在初始化", "INFO")
            
            # 重新初始化
            self.log_debug(f"重新初始化OCR引擎，模式: {precision_mode}", "INFO")
            success = OCRInvoice.OfflineOCRInvoice.global_initialize_ocr(precision_mode)
            
            if success:
                self.log_debug("[SUCCESS] OCR引擎重新初始化成功", "INFO")
                return True
            else:
                self.log_debug("[ERROR] OCR引擎重新初始化失败", "ERROR")
                QMessageBox.critical(
                    self,
                    "OCR引擎错误", 
                    f"OCR引擎初始化失败，无法处理文件。\n\n"
                    f"当前模式: {precision_mode}\n"
                    "请检查:\n"
                    "1. 模型文件是否完整\n"
                    "2. 系统内存是否充足\n"
                    "3. 依赖库是否正确安装\n\n"
                    "您可以通过【调试工具】查看详细错误信息。"
                )
                return False
                
        except Exception as e:
            self.log_debug(f"[ERROR] ensure_ocr_ready异常: {e}", "ERROR")
            QMessageBox.critical(self, "系统错误", f"OCR状态检查失败:\n{str(e)}")
            return False
    
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
        
        # PDF处理按钮（文件多选）
        self.pdf_button = QPushButton("🗃️ 处理PDF文件（可多选）")
        self.pdf_button.clicked.connect(self.handle_pdf_file)
        actions_layout.addWidget(self.pdf_button)
        
        # PDF文件夹处理按钮（递归处理所有PDF）
        self.pdf_folder_button = QPushButton("📂 处理PDF文件夹（含子目录）")
        self.pdf_folder_button.clicked.connect(self.handle_pdf_folder)
        actions_layout.addWidget(self.pdf_folder_button)
        
        # 图片处理按钮（图片文件夹）
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
        
        # 调试组
        debug_group = QGroupBox("🔧 调试工具")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_btn = QPushButton("🐛 显示调试日志")
        self.debug_btn.clicked.connect(self.show_debug_log)
        debug_layout.addWidget(self.debug_btn)
        
        self.test_ocr_btn = QPushButton("🧪 测试OCR功能")
        self.test_ocr_btn.clicked.connect(self.test_ocr_function)
        debug_layout.addWidget(self.test_ocr_btn)
        
        self.diagnostic_btn = QPushButton("🔍 系统诊断")
        self.diagnostic_btn.clicked.connect(self.run_system_diagnostic)
        debug_layout.addWidget(self.diagnostic_btn)
        
        control_layout.addWidget(debug_group)
        
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
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["开票公司名称", "发票号码", "发票日期", "项目名称", "金额（价税合计）"])
        
        # 设置表格属性
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.verticalHeader().setVisible(False)
        
        # 设置列宽自适应
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 开票公司名称列自适应内容
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 发票号码列自适应内容
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 发票日期列自适应内容
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 项目名称列自适应内容
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 金额列自适应内容
        
        self.result_tabs.addTab(self.result_table, "📋 识别结果")
        
        # 原始数据选项卡
        self.raw_data_text = QTextEdit()
        self.raw_data_text.setReadOnly(True)
        self.raw_data_text.setFont(QtGui.QFont("Consolas", 10))
        self.result_tabs.addTab(self.raw_data_text, "📊 原始数据")
        
        # 调试日志选项卡
        self.debug_log_text = QTextEdit()
        self.debug_log_text.setReadOnly(True)
        self.debug_log_text.setFont(QtGui.QFont("Consolas", 9))
        self.debug_log_text.setStyleSheet("QTextEdit { background-color: #1e1e1e; color: #ffffff; }")
        self.result_tabs.addTab(self.debug_log_text, "🔍 调试日志")
        
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
        self.status_label = QtWidgets.QLabel("[SUCCESS] 就绪 - 离线运行" if self.offline_status else "⚠️ 就绪 - 需要网络")
        
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
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #007bff;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QTableWidget::item:selected {
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
                model_info += "\n状态: [SUCCESS] 可完全离线运行"
                
            else:
                model_info = "未找到本地模型文件\n\n请通过【工具】→【模型配置】复制模型"
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
                # [文件路径, 开票公司名称, 发票号码, 发票日期, 金额（价税合计）, 项目名称]
                company_name = str(result[1]) if result[1] else ""
                # 清理开票公司名称的前缀
                if company_name.startswith("名称："):
                    company_name = company_name[3:]  # 去掉"名称："前缀
                
                invoice_number = str(result[2]) if result[2] else ""
                invoice_date = str(result[3]) if result[3] else ""
                invoice_amount = str(result[4]) if result[4] else ""  # 金额（价税合计）
                project_name = str(result[5]) if result[5] else ""  # 项目名称
                
                # 设置单元格内容（去掉文件路径列）
                self.result_table.setItem(row, 0, QTableWidgetItem(company_name))
                self.result_table.setItem(row, 1, QTableWidgetItem(invoice_number))
                self.result_table.setItem(row, 2, QTableWidgetItem(invoice_date))
                self.result_table.setItem(row, 3, QTableWidgetItem(project_name))  # 项目名称
                self.result_table.setItem(row, 4, QTableWidgetItem(invoice_amount))  # 金额（价税合计）
                
                # 设置工具提示显示完整路径
                self.result_table.item(row, 0).setToolTip(str(result[0]))
            elif isinstance(result, list) and len(result) >= 5:
                # 兼容旧格式（5个字段）
                # [文件路径, 开票公司名称, 发票号码, 日期, 金额(价税合计)]
                company_name = str(result[1]) if result[1] else ""
                # 清理开票公司名称的前缀
                if company_name.startswith("名称："):
                    company_name = company_name[3:]  # 去掉"名称："前缀
                
                invoice_number = str(result[2]) if result[2] else ""
                invoice_date = str(result[3]) if result[3] else ""
                invoice_amount = str(result[4]) if result[4] else ""
                
                # 设置单元格内容（去掉文件路径列）
                self.result_table.setItem(row, 0, QTableWidgetItem(company_name))
                self.result_table.setItem(row, 1, QTableWidgetItem(invoice_number))
                self.result_table.setItem(row, 2, QTableWidgetItem(invoice_date))
                self.result_table.setItem(row, 3, QTableWidgetItem(""))  # 项目名称为空
                self.result_table.setItem(row, 4, QTableWidgetItem(invoice_amount))  # 金额（价税合计）
                
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
        self.debug_log_text.clear()
        self.export_btn.setEnabled(False)
    
    def log_debug(self, message, level="INFO"):
        """添加调试日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # 在控制台输出
        print(log_entry.strip())
        
        # 在调试日志窗口显示（如果组件已经创建）
        if hasattr(self, 'debug_log_text') and self.debug_log_text:
            self.debug_log_text.moveCursor(QtGui.QTextCursor.End)
            self.debug_log_text.insertPlainText(log_entry)
            self.debug_log_text.ensureCursorVisible()
    
    def show_debug_log(self):
        """显示调试日志窗口"""
        self.result_tabs.setCurrentWidget(self.debug_log_text)
        self.log_debug("调试日志窗口已打开", "DEBUG")
    
    def test_ocr_function(self):
        """测试OCR功能"""
        self.log_debug("开始测试OCR功能...", "INFO")
        self.result_tabs.setCurrentWidget(self.debug_log_text)
        
        try:
            # 导入OCR模块
            self.log_debug("导入OCRInvoice模块...", "DEBUG")
            import OCRInvoice
            
            self.log_debug("创建OCR实例...", "DEBUG")
            ocr = OCRInvoice.OfflineOCRInvoice()
            
            self.log_debug("检查离线配置...", "DEBUG")
            self.log_debug(f"配置信息: {ocr.offline_config}", "DEBUG")
            
            self.log_debug("检查模型文件...", "DEBUG")
            models_available, model_message = ocr.check_models_available()
            if models_available:
                self.log_debug("[SUCCESS] 模型文件检查通过", "INFO")
            else:
                self.log_debug(f"[ERROR] 模型文件检查失败: {model_message}", "ERROR")
                return
            
            self.log_debug("初始化OCR引擎...", "DEBUG")
            if ocr.initialize_ocr():
                self.log_debug("[SUCCESS] OCR引擎初始化成功", "INFO")
                
                # 创建测试图片
                self.log_debug("创建测试图片...", "DEBUG")
                from PIL import Image
                import numpy as np
                
                test_img = Image.new('RGB', (200, 100), color='white')
                test_img_array = np.array(test_img)
                
                self.log_debug("执行OCR识别...", "DEBUG")
                try:
                    result = ocr.ocr_engine.ocr(test_img_array)
                    self.log_debug(f"[SUCCESS] OCR识别成功: {result}", "INFO")
                except Exception as ocr_error:
                    self.log_debug(f"[ERROR] OCR识别失败: {str(ocr_error)}", "ERROR")
                    import traceback
                    self.log_debug(f"OCR错误详情: {traceback.format_exc()}", "ERROR")
                    
            else:
                self.log_debug("[ERROR] OCR引擎初始化失败", "ERROR")
                
        except Exception as e:
            self.log_debug(f"[ERROR] OCR功能测试失败: {str(e)}", "ERROR")
            import traceback
            self.log_debug(f"错误详情:\n{traceback.format_exc()}", "ERROR")
    
    def run_system_diagnostic(self):
        """运行系统诊断"""
        self.log_debug("开始系统诊断...", "INFO")
        self.result_tabs.setCurrentWidget(self.debug_log_text)
        
        try:
            # 检查Python环境
            self.log_debug(f"Python版本: {sys.version}", "INFO")
            self.log_debug(f"当前工作目录: {os.getcwd()}", "INFO")
            self.log_debug(f"可执行路径: {sys.executable}", "INFO")
            
            # 检查关键模块
            critical_modules = [
                ('PyQt5', 'PyQt5.QtWidgets'),
                ('NumPy', 'numpy'),
                ('Pandas', 'pandas'),
                ('PIL', 'PIL'),
                ('OpenCV', 'cv2'),
                ('PyMuPDF', 'fitz'),
                ('scikit-image', 'skimage')
            ]
            
            # PaddleOCR 相关模块 - 一次性检查所有依赖（移除PaddleX依赖以减少打包耦合）
            paddle_modules = [
                ('PaddleOCR', 'paddleocr'),
                ('PaddlePaddle', 'paddle'),
                ('huggingface_hub', 'huggingface_hub'),
            ]
            
            self.log_debug("检查关键模块依赖:", "INFO")
            critical_errors = []
            for name, module in critical_modules:
                try:
                    __import__(module)
                    self.log_debug(f"  [SUCCESS] {name}", "INFO")
                except ImportError as e:
                    self.log_debug(f"  [ERROR] {name}: {str(e)}", "ERROR")
                    critical_errors.append((name, str(e)))
            
            self.log_debug("检查PaddleOCR相关模块:", "INFO")
            paddle_errors = []
            
            # 使用更robust的方法检查PaddleOCR相关模块
            for name, module in paddle_modules:
                try:
                    # 特殊处理PaddleOCR主模块
                    if module == 'paddleocr':
                        try:
                            __import__(module)
                            self.log_debug(f"  [SUCCESS] {name}", "INFO")
                        except ImportError as e:
                            self.log_debug(f"  [ERROR] {name}: {str(e)}", "ERROR")
                            paddle_errors.append((name, str(e)))
                    else:
                        # 对于子模块，使用更安全的检查方式
                        try:
                            # 先检查父模块
                            parent_module = module.split('.')[0]
                            __import__(parent_module)
                            
                            # 然后尝试检查子模块
                            try:
                                __import__(module)
                                self.log_debug(f"  [SUCCESS] {name}", "INFO")
                            except ImportError as e:
                                self.log_debug(f"  [ERROR] {name}: {str(e)}", "ERROR")
                                paddle_errors.append((name, str(e)))
                        except ImportError as e:
                            self.log_debug(f"  [ERROR] {name}: {parent_module} 主模块缺失", "ERROR")
                            paddle_errors.append((name, f"父模块 {parent_module} 缺失"))
                except Exception as e:
                    # 捕获其他异常，防止程序中断
                    self.log_debug(f"  [ERROR] {name}: {str(e)}", "ERROR")
                    paddle_errors.append((name, str(e)))
            
            # 已移除 PaddleX 子模块扫描，避免无关错误提示
            
            # 一次性显示所有导入错误汇总
            all_errors = critical_errors + paddle_errors
            if all_errors:
                self.log_debug("", "INFO")
                self.log_debug("=== 系统导入错误汇总 ===", "ERROR")
                self.log_debug(f"共发现 {len(all_errors)} 个模块导入失败:", "ERROR")
                
                # 分组显示错误
                if critical_errors:
                    self.log_debug("关键模块错误:", "ERROR")
                    for name, error in critical_errors:
                        self.log_debug(f"  - {name}: {error}", "ERROR")
                
                if paddle_errors:
                    self.log_debug("PaddleOCR相关模块错误:", "ERROR")
                    for name, error in paddle_errors:
                        self.log_debug(f"  - {name}: {error}", "ERROR")
                
                self.log_debug("", "ERROR")
                
                # 提供解决方案建议
                if critical_errors:
                    self.log_debug("关键模块解决方案:", "ERROR")
                    self.log_debug("请安装缺失的关键模块:", "ERROR")
                    self.log_debug("pip install numpy pandas pillow opencv-contrib-python pymupdf scikit-image", "ERROR")
                
                if paddle_errors:
                    self.log_debug("PaddleOCR模块解决方案:", "ERROR")
                    self.log_debug("请安装/修复缺失的 PaddleOCR 相关依赖，或使用内置打包流程（Embedded Python）而非 PyInstaller。", "ERROR")
                    hiddenimports_list = [module for name, module in paddle_errors]
                    self.log_debug(f"  相关模块: {', '.join(hiddenimports_list)}", "ERROR")
            
            # 检查模型文件
            self.log_debug("检查模型文件:", "INFO")
            model_paths = [
                "models/PP-OCRv5_mobile_det",
                "models/PP-OCRv5_mobile_rec", 
                "models/ch_ppocr_mobile_v2.0_cls"
            ]
            
            for model_path in model_paths:
                if os.path.exists(model_path):
                    self.log_debug(f"  [SUCCESS] {model_path}", "INFO")
                    # 检查关键文件
                    required_files = ["inference.pdiparams", "inference.yml"]
                    for file in required_files:
                        file_path = os.path.join(model_path, file)
                        if os.path.exists(file_path):
                            self.log_debug(f"    [SUCCESS] {file}", "INFO")
                        else:
                            self.log_debug(f"    [ERROR] {file}", "ERROR")
                else:
                    self.log_debug(f"  [ERROR] {model_path}", "ERROR")
            
            # 检查配置文件
            self.log_debug("检查配置文件:", "INFO")
            if os.path.exists("offline_config.json"):
                self.log_debug("  [SUCCESS] offline_config.json", "INFO")
                try:
                    import json
                    with open("offline_config.json", 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        self.log_debug(f"  配置内容: {config}", "DEBUG")
                except Exception as e:
                    self.log_debug(f"  [ERROR] 配置文件读取失败: {str(e)}", "ERROR")
            else:
                self.log_debug("  [ERROR] offline_config.json 不存在", "ERROR")
            
            # 检查系统DLL
            self.log_debug("检查系统DLL:", "INFO")
            import subprocess
            try:
                result = subprocess.run(['where', 'vcruntime140.dll'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.log_debug(f"  [SUCCESS] vcruntime140.dll: {result.stdout.strip()}", "INFO")
                else:
                    self.log_debug("  [ERROR] vcruntime140.dll: 未找到", "WARNING")
            except Exception as e:
                self.log_debug(f"  [ERROR] 检查vcruntime140.dll失败: {str(e)}", "ERROR")
            
            self.log_debug("系统诊断完成", "INFO")
            
        except Exception as e:
            self.log_debug(f"系统诊断失败: {str(e)}", "ERROR")
            import traceback
            self.log_debug(f"错误详情:\n{traceback.format_exc()}", "ERROR")
    
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
                        company_name = str(result[1]) if result[1] else ""
                        # 清理开票公司名称的前缀
                        if company_name.startswith("名称："):
                            company_name = company_name[3:]  # 去掉"名称："前缀
                        
                        data_dict = {
                            "开票公司名称": company_name,
                            "发票号码": str(result[2]) if result[2] else "",
                            "发票日期": str(result[3]) if result[3] else "",
                            "项目名称": str(result[5]) if result[5] else "",
                            "金额（价税合计）": str(result[4]) if result[4] else ""
                        }
                        data_list.append(data_dict)
                    elif isinstance(result, list) and len(result) >= 5:
                        # 兼容旧格式（5个字段）
                        company_name = str(result[1]) if result[1] else ""
                        # 清理开票公司名称的前缀
                        if company_name.startswith("名称："):
                            company_name = company_name[3:]  # 去掉"名称："前缀
                        
                        data_dict = {
                            "开票公司名称": company_name,
                            "发票号码": str(result[2]) if result[2] else "",
                            "发票日期": str(result[3]) if result[3] else "",
                            "项目名称": "",
                            "金额（价税合计）": result[4] if result[4] else ""
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
        self.log_debug("准备处理PDF文件...", "INFO")
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            '选择PDF文件（可多选）', 
            './', 
            'PDF文件 (*.pdf)'
        )
        
        if file_paths:
            self.log_debug(f"选择的PDF文件数: {len(file_paths)}", "INFO")
            precision_mode = self.precision_combo.currentText()
            self.log_debug(f"精度模式: {precision_mode}", "DEBUG")
            
            # 🔥 检查OCR引擎状态，必要时重新初始化
            if not self.ensure_ocr_ready(precision_mode):
                return
            
            try:
                # 创建并启动PDF批量处理线程
                self.pdf_thread = PDFBatchOCRThread()
                self.pdf_thread.files = file_paths
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
                if len(file_paths) == 1:
                    self.update_status(f"📄 开始处理PDF: {os.path.basename(file_paths[0])}")
                else:
                    self.update_status(f"📄 开始批量处理PDF: {len(file_paths)} 个")
                self.log_debug("启动PDF批量处理线程...", "DEBUG")
                self.pdf_thread.start()
                
            except Exception as e:
                self.log_debug(f"PDF处理失败: {str(e)}", "ERROR")
                import traceback
                self.log_debug(f"错误详情:\n{traceback.format_exc()}", "ERROR")
                QMessageBox.critical(self, "错误", f"PDF处理失败:\n{str(e)}")
        else:
            self.log_debug("用户取消了PDF文件选择", "DEBUG")
    
    def handle_image_folder(self):
        """处理图片文件夹"""
        self.log_debug("准备处理图片文件夹...", "INFO")
        
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            '选择包含图片的文件夹', 
            './'
        )
        
        if folder_path:
            self.log_debug(f"选择的图片文件夹: {folder_path}", "INFO")
            precision_mode = self.precision_combo.currentText()
            self.log_debug(f"精度模式: {precision_mode}", "DEBUG")
            
            # 🔥 检查OCR引擎状态，必要时重新初始化
            if not self.ensure_ocr_ready(precision_mode):
                return
            
            try:
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
                self.log_debug("启动图片处理线程...", "DEBUG")
                self.image_thread.start()
                
            except Exception as e:
                self.log_debug(f"图片处理失败: {str(e)}", "ERROR")
                import traceback
                self.log_debug(f"错误详情:\n{traceback.format_exc()}", "ERROR")
                QMessageBox.critical(self, "错误", f"图片处理失败:\n{str(e)}")
        else:
            self.log_debug("用户取消了图片文件夹选择", "DEBUG")
    
    def handle_pdf_folder(self):
        """处理PDF文件夹（递归查找所有PDF）"""
        self.log_debug("准备处理PDF文件夹...", "INFO")
        
        folder_path = QFileDialog.getExistingDirectory(
            self,
            '选择包含PDF的文件夹',
            './'
        )
        
        if not folder_path:
            self.log_debug("用户取消了PDF文件夹选择", "DEBUG")
            return
        
        # 递归收集PDF
        pdf_files = []
        for root, dirs, files in os.walk(folder_path):
            for name in files:
                if name.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, name))
        
        if not pdf_files:
            QMessageBox.information(self, "提示", "所选文件夹中未发现PDF文件。")
            return
        
        self.log_debug(f"发现PDF文件 {len(pdf_files)} 个", "INFO")
        precision_mode = self.precision_combo.currentText()
        self.log_debug(f"精度模式: {precision_mode}", "DEBUG")
        
        # 🔥 检查OCR引擎状态，必要时重新初始化
        if not self.ensure_ocr_ready(precision_mode):
            return
        
        try:
            # 创建并启动PDF批量处理线程
            self.pdf_thread = PDFBatchOCRThread()
            self.pdf_thread.files = pdf_files
            self.pdf_thread.precision_mode = precision_mode
            self.pdf_thread.output_dir = self.output_dir
            self.pdf_thread.progress.connect(self.update_status)
            self.pdf_thread.result.connect(self.on_processing_result)
            self.pdf_thread.finished.connect(self.on_processing_finished)
            self.pdf_thread.ocr_result.connect(self.display_ocr_results)
            
            # 禁用按钮，显示进度条，开始处理
            self.set_buttons_enabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            folder_name = os.path.basename(folder_path) or folder_path
            self.update_status(f"📂 开始批量处理PDF（{folder_name}）：共 {len(pdf_files)} 个")
            self.log_debug("启动PDF批量处理线程（文件夹）...", "DEBUG")
            self.pdf_thread.start()
        
        except Exception as e:
            self.log_debug(f"PDF批量处理失败: {str(e)}", "ERROR")
            import traceback
            self.log_debug(f"错误详情:\n{traceback.format_exc()}", "ERROR")
            QMessageBox.critical(self, "错误", f"PDF批量处理失败:\n{str(e)}")
    
    def update_status(self, message):
        """更新状态显示"""
        self.status_label.setText(message)
        QApplication.processEvents()  # 强制更新UI
    
    def on_processing_result(self, result):
        """处理结果回调"""
        if result.get("success", False):
            file_type = result.get("type", "文件")
            self.update_status(f"[SUCCESS] {file_type}处理成功！")
        else:
            error = result.get("error", "未知错误")
            self.update_status(f"[ERROR] 处理失败: {error}")
    
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
        self.update_status(f"[SUCCESS] 就绪 - {mode_text}")
    
    def set_buttons_enabled(self, enabled):
        """设置按钮启用状态"""
        self.pdf_button.setEnabled(enabled)
        self.pdf_folder_button.setEnabled(enabled)
        self.image_button.setEnabled(enabled)
        self.precision_combo.setEnabled(enabled)
        self.model_status_btn.setEnabled(enabled)
        self.output_btn.setEnabled(enabled)  # 新增: 输出目录选择按钮
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 优先温和中止线程，超时后再强制结束
        for t in (self.pdf_thread, self.image_thread):
            try:
                if t and t.isRunning():
                    try:
                        t.requestInterruption()
                    except Exception:
                        pass
                    # 尝试优雅退出
                    if not t.wait(5000):
                        t.terminate()
                        t.wait(1000)
            except Exception:
                pass
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
                "- models/PP-OCRv5_mobile_det/\n"
                "- models/PP-OCRv5_mobile_rec/\n"
                "- models/ch_ppocr_mobile_v2.0_cls/\n\n"
                "您可以:\n"
                "1. 将现有模型文件夹复制到程序目录下\n"
                "2. 重新运行程序并在模型配置界面中设置正确路径"
            )
            sys.exit(1)
        
        print("[SUCCESS] 模型配置检查通过")
        
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
