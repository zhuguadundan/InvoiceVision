#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支持离线运行的OCRInvoice类 - PaddleOCR 3.1+ 离线版 (外部模型架构)
使用延迟导入避免打包时的模块依赖问题
"""

# 延迟导入 - 避免启动时就加载PaddleOCR
# from paddleocr import PaddleOCR  # 移到使用时导入
import re
import sys
from PIL import Image
import os
import json
import numpy as np
import cv2
from pathlib import Path
import threading
import time

def safe_print(text):
    """安全的打印函数，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('gbk', 'ignore').decode('gbk'))

class OfflineOCRInvoice:
    # 类变量：所有实例共享的OCR引擎
    _shared_ocr_engine = None
    _initialization_lock = threading.Lock()
    _initialization_status = "pending"  # pending, loading, ready, failed
    
    def __init__(self):
        """初始化离线OCR发票识别器"""
        self.precision_mode = '快速'
        self.offline_config = self._load_offline_config()
        
        # 确保全局OCR引擎已初始化
        if self.__class__._initialization_status == "pending":
            self.global_initialize_ocr()
        
    def _load_offline_config(self):
        """加载离线配置 - 支持外部模型架构"""
        try:
            # 导入resource_utils模块，支持打包环境
            import resource_utils
            base_dir = Path(resource_utils.get_resource_path("."))
            config_file = Path(resource_utils.get_config_path())
            # 使用resource_utils获取正确的模型路径
            models_path = Path(resource_utils.get_models_path())
        except ImportError:
            # 降级到原始逻辑
            base_dir = Path(__file__).parent
            config_file = base_dir / "offline_config.json"
            models_path = base_dir / "models"
        
        # 默认配置
        default_config = {
            "offline_mode": True,
            "use_gpu": False,
            "lang": "ch",
            "models_path": str(models_path)
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                        
            except Exception as e:
                print(f"配置文件加载失败，使用默认配置: {e}")
                config = default_config
        else:
            config = default_config
            
        # 使用resource_utils提供的模型路径，覆盖配置文件中的相对路径
        config["models_path"] = str(models_path)
        
        # 构建模型路径 - 使用正确的models_path
        if "models" not in config:
            config["models"] = {
                "cls_model_dir": str(models_path / "PP-LCNet_x1_0_textline_ori"),
                "det_model_dir": str(models_path / "PP-OCRv5_server_det"),
                "rec_model_dir": str(models_path / "PP-OCRv5_server_rec")
            }
        else:
            # 确保模型路径为绝对路径，使用正确的models_path
            for key, model_path in config["models"].items():
                model_name = Path(model_path).name
                config["models"][key] = str(models_path / model_name)
        
        return config
    
    def check_models_available(self):
        """检查模型文件是否可用"""
        if not self.offline_config or "models" not in self.offline_config:
            return False, "配置文件中未找到模型配置"
            
        print(f"[DEBUG] 模型基础路径: {self.offline_config.get('models_path', 'N/A')}")
        
        missing_models = []
        incomplete_models = []
        
        for model_name, model_path in self.offline_config["models"].items():
            print(f"[DEBUG] 检查模型 {model_name}: {model_path}")
            
            if not os.path.exists(model_path):
                missing_models.append(f"{model_name}: {model_path}")
                print(f"  [ERROR] 路径不存在")
            else:
                # 检查模型文件是否完整
                try:
                    files = os.listdir(model_path)
                    # 支持两种模型格式：新格式(inference.json)和旧格式(inference.pdmodel)
                    required_files_new = ['inference.json', 'inference.pdiparams']  # 新格式
                    required_files_old = ['inference.pdmodel', 'inference.pdiparams']  # 旧格式
                    
                    missing_files_new = [f for f in required_files_new if f not in files]
                    missing_files_old = [f for f in required_files_old if f not in files]
                    
                    if not missing_files_new:
                        print(f"  [OK] 模型文件完整 (新格式)")
                        print(f"    文件列表: {files}")
                    elif not missing_files_old:
                        print(f"  [OK] 模型文件完整 (旧格式)")
                        print(f"    文件列表: {files}")
                    else:
                        incomplete_models.append(f"{model_name}: 缺少文件 (新格式需要{missing_files_new} 或 旧格式需要{missing_files_old})")
                        print(f"  [ERROR] 缺少必需文件:")
                        print(f"    新格式缺少: {missing_files_new}")
                        print(f"    旧格式缺少: {missing_files_old}")
                        print(f"    当前文件: {files}")
                except Exception as e:
                    incomplete_models.append(f"{model_name}: 读取错误 {e}")
                    print(f"  [ERROR] 读取错误: {e}")
                
        error_messages = []
        if missing_models:
            error_messages.append("缺少模型文件夹:\n" + "\n".join(missing_models))
        if incomplete_models:
            error_messages.append("模型文件不完整:\n" + "\n".join(incomplete_models))
            
        if error_messages:
            return False, "\n\n".join(error_messages)
            
        return True, "所有模型文件已就绪"
    
    @classmethod
    def global_initialize_ocr(cls, precision_mode='快速'):
        """全局OCR引擎初始化 - 在主线程中调用，避免重复初始化"""
        with cls._initialization_lock:
            if cls._initialization_status == "ready":
                print("OCR引擎已经初始化完成")
                return True
            
            if cls._initialization_status == "loading":
                # 等待初始化完成
                print("OCR引擎正在初始化中，等待完成...")
                timeout = 30  # 30秒超时
                start_time = time.time()
                while cls._initialization_status == "loading" and time.time() - start_time < timeout:
                    time.sleep(0.1)
                return cls._initialization_status == "ready"
            
            cls._initialization_status = "loading"
            print(f"开始全局初始化OCR引擎，精度模式: {precision_mode}")
            
            try:
                # 在主线程中设置环境变量 - 必须在导入前设置
                os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
                os.environ['PADDLE_DISABLE_SHARED_MEM'] = '1'
                os.environ['CUDA_VISIBLE_DEVICES'] = ''
                print("环境变量设置完成")
                
                # 创建临时实例获取配置
                temp_instance = cls()
                models_available, message = temp_instance.check_models_available()
                if not models_available:
                    cls._initialization_status = "failed"
                    print(f"模型检查失败: {message}")
                    return False
                
                models = temp_instance.offline_config.get("models", {})
                
                # 仅使用 PaddleOCR 初始化
                from paddleocr import PaddleOCR
                print("PaddleOCR模块导入成功")
                
                # 使用官方OCR pipeline
                cls._shared_ocr_engine = PaddleOCR(use_angle_cls=precision_mode == '高精', lang='ch')
                cls._initialization_status = "ready"
                print("[SUCCESS] 全局PaddleOCR引擎初始化成功")
                return True
                        
            except ImportError as e:
                cls._initialization_status = "failed"
                print(f"[ERROR] OCR模块导入失败: {e}")
                return False
            except Exception as e:
                cls._initialization_status = "failed"
                print(f"[ERROR] 全局OCR引擎初始化失败: {e}")
                print(f"错误类型: {type(e).__name__}")
                import traceback
                print(f"详细错误信息:\n{traceback.format_exc()}")
                return False
    
    @property
    def ocr_engine(self):
        """获取共享的OCR引擎实例"""
        return self.__class__._shared_ocr_engine
    
    @classmethod
    def get_initialization_status(cls):
        """获取初始化状态"""
        return cls._initialization_status
    
    def initialize_ocr(self):
        """旧版初始化方法 - 现在委托给全局初始化"""
        print("调用旧版initialize_ocr，委托给全局初始化...")
        return self.__class__._shared_ocr_engine is not None
    
    def set_precision_mode(self, mode):
        """设置精度模式 - 需要重新全局初始化"""
        if mode in ['快速', '高精']:
            self.precision_mode = mode
            print(f"精度模式设置为: {mode}")
            print("注意: 精度模式更改需要重新调用 global_initialize_ocr() 才能生效")
            return True
        else:
            print("无效的精度模式，支持的模式: '快速', '高精'")
            return False
    
    def run_ocr(self, image_path):
        """执行OCR识别"""
        # 检查全局OCR引擎是否可用
        if self.ocr_engine is None:
            print("ERROR: 全局OCR引擎未初始化，请先调用 OfflineOCRInvoice.global_initialize_ocr()")
            return [image_path, '', '', '', '']
        
        try:
            print(f"开始处理图片: {os.path.basename(image_path)}")
            
            # 读取图片
            try:
                # 方法1: 使用cv2直接读取
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    raise Exception("图像解码失败")
            except:
                # 方法2: 使用PIL作为后备方案
                from PIL import Image
                pil_image = Image.open(image_path)
                img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # 执行OCR识别（PaddleOCR）
            result = self.ocr_engine.ocr(img)
            texts = self._extract_texts_from_result(result)
            
            if not texts:
                print("OCR未识别到任何文本")
                return [image_path, '', '', '', '']
            
            # 检查是否识别到发票内容
            combined_text = '【' + '】【'.join(texts) + '】'
            
            if not self._contains_invoice_keywords(combined_text):
                print("未检测到发票关键词，尝试旋转图片...")
                img_rotated = cv2.rotate(img, cv2.ROTATE_180)
                
                # 旋转后再次OCR识别（PaddleOCR）
                result = self.ocr_engine.ocr(img_rotated)
                texts = self._extract_texts_from_result(result)
                combined_text = '【' + '】【'.join(texts) + '】'
            
            # 提取发票信息
            invoice_info = self._extract_invoice_info(combined_text, image_path)
            print(f"识别完成: {os.path.basename(image_path)}")
            return invoice_info
            
        except Exception as e:
            print(f"OCR处理出错: {e}")
            return [image_path, '', '', '', '']
    
    def _extract_texts_from_result(self, result):
        """从OCR结果中提取文本"""
        texts = []
        try:
            if result and len(result) > 0:
                # 检查新格式的结果（PaddleX/PaddleOCR新版本）
                if isinstance(result[0], dict) and 'rec_texts' in result[0]:
                    # 新版本格式：结果包含rec_texts字段
                    texts = result[0]['rec_texts']
                    print("使用新格式提取文本，共{}条".format(len(texts)))
                elif result[0]:
                    # 旧版本格式
                    ocr_result = result[0]
                    for line in ocr_result:
                        if line and len(line) > 1 and line[1]:
                            if isinstance(line[1], tuple) and len(line[1]) > 0:
                                text = line[1][0].strip()
                            elif isinstance(line[1], str):
                                text = line[1].strip()
                            else:
                                continue
                            
                            if text:
                                texts.append(text)
                    print("使用旧格式提取文本，共{}条".format(len(texts)))
        except (IndexError, TypeError) as e:
            print(f"文本提取出错: {e}")
        return texts
    
    # 已移除 EasyOCR 解析路径，仅保留 PaddleOCR
    
    def _contains_invoice_keywords(self, text):
        """检查文本是否包含发票关键词"""
        keywords = ['发票', '增值税', '专用发票', '普通发票', '发票号码', '发票代码']
        return any(keyword in text for keyword in keywords)
    
    def _extract_invoice_info(self, text, image_path):
        """从文本中提取发票信息"""
        company_name = ''
        invoice_number = ''
        invoice_date = ''
        invoice_amount = ''
        project_name = ''  # 新增项目名称字段
        
        print(f"提取信息的文本: {text}")
        
        try:
            # 提取开票公司名称 - 更灵活的匹配方式
            company_patterns = [
                r'销售方名称[：:]\s*([^\n\r【】]{2,100}?)(?=\s*【|$)',
                r'销售方[：:]\s*([^\n\r【】]{2,100}?)(?=\s*【|$)',
                r'开票方名称[：:]\s*([^\n\r【】]{2,100}?)(?=\s*【|$)',
                r'开票方[：:]\s*([^\n\r【】]{2,100}?)(?=\s*【|$)',
                r'销售单位[：:]\s*([^\n\r【】]{2,100}?)(?=\s*【|$)',
                r'收款单位[：:]\s*([^\n\r【】]{2,100}?)(?=\s*【|$)',
            ]
            
            for pattern in company_patterns:
                company_matches = re.findall(pattern, text)
                if company_matches:
                    for match in company_matches:
                        match = match.strip()
                        # 清理可能的前缀
                        match = re.sub(r'^[销售开票收款]方[名称单位]*[：:]', '', match).strip()
                        # 更宽松的验证条件
                        if (len(match) >= 2 and not match[0].isdigit() and 
                            not any(word in match for word in ['发票', '号码', '日期', '金额', '项目'])):
                            company_name = match
                            print(f"提取到开票公司名称: {company_name}")
                            break
                    if company_name:
                        break
            
            # 如果上述模式未匹配到，尝试更宽松的模式
            if not company_name:
                # 尝试匹配包含"公司"、"厂"、"店"等关键词的文本
                company_loose_pattern = r'([^\n\r【】]{1,50}(?:公司|厂|店|中心|集团|企业)[^\n\r【】]{0,30})'
                company_loose_matches = re.findall(company_loose_pattern, text)
                for match in company_loose_matches:
                    match = match.strip()
                    # 过滤掉明显不是公司名称的内容
                    if (len(match) >= 3 and not match[0].isdigit() and 
                        not any(word in match for word in ['发票', '号码', '日期', '金额', '项目', '购买方', '买方'])):
                        company_name = match
                        print(f"通过宽松模式提取到开票公司名称: {company_name}")
                        break
        except Exception as e:
            print(f"开票公司名称提取失败: {e}")
        
        # 最终清理开票公司名称中的"名称："前缀
        if company_name and company_name.startswith("名称："):
            company_name = company_name[3:].strip()  # 去掉"名称："前缀
            print(f"清理前缀后的开票公司名称: {company_name}")
        
        try:
            # 提取发票号码
            number_patterns = [
                r'发票号码[：:]】?【?([0-9]{6,20})',  # 处理【发票号码：】【数字】的格式
                r'发票号码[：:]\s*([0-9]{6,20})',
                r'发票号[：:]?\s*([0-9]{6,20})',
                r'号码[：:]\s*([0-9]{6,20})',
                r'No[：:.]?\s*([0-9]{6,20})',
                r'【([0-9]{15,20})】',  # 直接匹配长数字（发票号码通常很长）
            ]
            
            for pattern in number_patterns:
                number_matches = re.findall(pattern, text)
                if number_matches:
                    invoice_number = number_matches[0]
                    print(f"提取到发票号码: {invoice_number}")
                    break
        except Exception as e:
            print(f"发票号码提取失败: {e}")
        
        try:
            # 提取发票日期 - 支持多种格式，修复日期错误提取金额的问题
            date_patterns = [
                r'发票日期[：:]\s*([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日',  # YYYY年MM月DD日
                r'开票日期[：:]\s*([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日',  # 开票日期
                r'日期[：:]\s*([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日',      # 日期
                r'([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日',                 # 直接日期格式
                r'发票日期[：:]\s*([0-9]{4})[.-]([0-9]{1,2})[.-]([0-9]{1,2})', # YYYY-MM-DD或YYYY.MM.DD
                r'开票日期[：:]\s*([0-9]{4})[.-]([0-9]{1,2})[.-]([0-9]{1,2})', # 开票日期YYYY-MM-DD
                r'([0-9]{4})[.-]([0-9]{1,2})[.-]([0-9]{1,2})',               # 直接YYYY-MM-DD格式
            ]
            
            for pattern in date_patterns:
                date_matches = re.findall(pattern, text)
                if date_matches:
                    match = date_matches[0]
                    if isinstance(match, tuple) and len(match) >= 3:
                        year, month, day = match[0], match[1], match[2]
                    else:
                        # 如果是字符串格式，尝试分割
                        date_str = match if isinstance(match, str) else str(match)
                        parts = re.split(r'[-年月日.]', date_str)
                        if len(parts) >= 3:
                            year, month, day = parts[0], parts[1], parts[2]
                        else:
                            continue
                    
                    # 确保是有效的日期格式
                    try:
                        year, month, day = int(year), int(month), int(day)
                        if 2000 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                            invoice_date = f"{year}{month:02d}{day:02d}"
                            print(f"提取到发票日期: {invoice_date}")
                            break
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            print(f"发票日期提取失败: {e}")
        
        try:
            # 提取发票金额 - 优先提取价税合计/实付金额
            invoice_amount = ""
            
            # 第一优先级：价税合计相关
            priority_patterns = [
                r'价税合计[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)',  # 价税合计：123.45
                r'价税合计[：:][^￥¥\d]*([0-9]+\.?[0-9]*)\s*[￥¥]?',  # 价税合计：￥123.45
                r'实付金额[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)',  # 实付金额：123.45
                r'实付[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)',     # 实付：123.45
                r'应付金额[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)', # 应付金额：123.45
                r'总计[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)',     # 总计：123.45
                r'总金额[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)',   # 总金额：123.45
            ]
            
            # 尝试第一优先级模式
            for pattern in priority_patterns:
                amount_matches = re.findall(pattern, text)
                if amount_matches:
                    valid_amounts = []
                    for amount_str in amount_matches:
                        try:
                            amount = float(amount_str)
                            # 过滤掉可能的错误匹配（比如日期数字）
                            if amount >= 0.01 and amount <= 999999999:  # 限制合理范围
                                valid_amounts.append(amount)
                        except ValueError:
                            continue
                    
                    if valid_amounts:
                        invoice_amount = max(valid_amounts)  # 取最大的金额作为发票总额
                        print(f"通过优先模式提取到发票金额: {invoice_amount} (模式: {pattern})")
                        break
            
            # 第二优先级：如果没有找到价税合计，尝试其他模式
            if not invoice_amount:
                secondary_patterns = [
                    r'合计[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)',     # 合计：123.45
                    r'小写[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)',     # 小写：123.45
                    r'金额[（\(]含税[）\)][：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)', # 金额（含税）：123.45
                ]
                
                for pattern in secondary_patterns:
                    amount_matches = re.findall(pattern, text)
                    if amount_matches:
                        valid_amounts = []
                        for amount_str in amount_matches:
                            try:
                                amount = float(amount_str)
                                if amount >= 0.01 and amount <= 999999999:
                                    valid_amounts.append(amount)
                            except ValueError:
                                continue
                        
                        if valid_amounts:
                            invoice_amount = max(valid_amounts)
                            print(f"通过次要模式提取到发票金额: {invoice_amount} (模式: {pattern})")
                            break
            
            # 第三优先级：通用金额模式（最后备用）
            if not invoice_amount:
                fallback_patterns = [
                    r'[￥¥]\s*([0-9]+\.?[0-9]*)',  # ￥123.45
                ]
                
                for pattern in fallback_patterns:
                    amount_matches = re.findall(pattern, text)
                    if amount_matches:
                        # 对于通用模式，取最后一个（通常是价税合计）
                        try:
                            amount = float(amount_matches[-1])  # 取最后一个金额
                            if amount >= 0.01 and amount <= 999999999:
                                invoice_amount = amount
                                print(f"通过备用模式提取到发票金额: {invoice_amount} (最后一个金额)")
                                break
                        except ValueError:
                            continue
        except Exception as e:
            print(f"发票金额提取失败: {e}")
        
        try:
            # 提取项目名称 - 根据用户描述格式【*体育用品*Keep动感单车】
            # 匹配包含*的项目名称格式
            project_patterns = [
                r'【\*([^\*】]+)\*([^\*】]+)】',  # 格式如【*体育用品*Keep动感单车】
                r'项目名称[：:]\s*([^\n\r【】]+?)(?=\s*【|$)',
                r'项目[：:]\s*([^\n\r【】]+?)(?=\s*【|$)',
                r'商品名称[：:]\s*([^\n\r【】]+?)(?=\s*【|$)',
                r'名称[：:]\s*([^\n\r【】]+?)(?=\s*【|$)',
                r'服务名称[：:]\s*([^\n\r【】]+?)(?=\s*【|$)',
                r'费用名称[：:]\s*([^\n\r【】]+?)(?=\s*【|$)',
            ]
            
            for pattern in project_patterns:
                project_matches = re.findall(pattern, text)
                print(f"项目名称模式 '{pattern}' 匹配结果: {project_matches}")
                if project_matches:
                    if isinstance(project_matches[0], tuple) and len(project_matches[0]) >= 2:
                        # 对于【*体育用品*Keep动感单车】格式，取第二部分作为项目名称
                        project_name = project_matches[0][1].strip()
                    else:
                        project_name = project_matches[0].strip() if isinstance(project_matches[0], str) else str(project_matches[0]).strip()
                    
                    # 清理项目名称
                    project_name = re.sub(r'[【】\*]', '', project_name).strip()
                    if project_name and len(project_name) > 1:
                        print(f"提取到项目名称: {project_name}")
                        break
                    else:
                        project_name = ''
        except Exception as e:
            print(f"项目名称提取失败: {e}")
        
        result = [image_path, company_name, invoice_number, invoice_date, invoice_amount, project_name]
        print(f"最终提取结果: {result}")
        return result

    def get_model_info(self):
        """获取当前使用的模型信息"""
        info = {
            "precision_mode": self.precision_mode,
            "offline_mode": self.offline_config is not None,
            "initialized": self.ocr_engine is not None
        }
        
        if self.offline_config:
            info["models_path"] = self.offline_config.get("models_path", "")
            info["available_models"] = list(self.offline_config.get("models", {}).keys())
            
            # 检查模型状态
            models_available, message = self.check_models_available()
            info["models_status"] = message
            info["models_available"] = models_available
        
        return info

# 保持向后兼容性
OCRInvoice = OfflineOCRInvoice

if __name__ == '__main__':
    # 测试代码
    print("=" * 60)
    print("离线OCR发票识别器测试 (外部模型架构)")
    print("=" * 60)
    
    ocr_invoice = OfflineOCRInvoice()
    
    # 显示模型信息
    model_info = ocr_invoice.get_model_info()
    print("模型信息:")
    for key, value in model_info.items():
        print(f"  {key}: {value}")
    
    # 检查模型可用性
    models_available, message = ocr_invoice.check_models_available()
    print(f"\n模型状态: {message}")
    
    if models_available:
        print("\n[OK] 模型文件检查通过，可以进行OCR识别")
        # 这里可以添加实际的图片测试
    else:
        print("\n[ERROR] 模型文件缺失，请使用模型管理器配置模型文件")