#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支持离线运行的OCRInvoice类 - PaddleOCR 3.1+ 离线版 (外部模型架构)
使用延迟导入避免打包时的模块依赖问题
"""

# 延迟导入 - 避免启动时就加载PaddleOCR
# from paddleocr import PaddleOCR  # 移到使用时导入
import re
from PIL import Image
import os
import json
import numpy as np
import cv2
from pathlib import Path

class OfflineOCRInvoice:
    def __init__(self):
        """初始化离线OCR发票识别器"""
        self.precision_mode = '快速'
        self.ocr_engine = None
        self.offline_config = self._load_offline_config()
        
    def _load_offline_config(self):
        """加载离线配置 - 支持外部模型架构"""
        base_dir = Path(__file__).parent
        config_file = base_dir / "offline_config.json"
        
        # 默认配置
        default_config = {
            "offline_mode": True,
            "use_gpu": False,
            "lang": "ch",
            "models_path": "models"
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
            
        # 确保模型路径是绝对路径
        models_path = Path(config.get("models_path", "models"))
        if not models_path.is_absolute():
            models_path = base_dir / models_path
            
        config["models_path"] = str(models_path)
        
        # 构建模型路径
        if "models" not in config:
            config["models"] = {
                "cls_model_dir": str(models_path / "PP-LCNet_x1_0_textline_ori"),
                "det_model_dir": str(models_path / "PP-OCRv5_server_det"),
                "rec_model_dir": str(models_path / "PP-OCRv5_server_rec")
            }
        else:
            # 确保模型路径为绝对路径
            for key, model_path in config["models"].items():
                if not Path(model_path).is_absolute():
                    config["models"][key] = str(models_path / Path(model_path).name)
        
        return config
    
    def check_models_available(self):
        """检查模型文件是否可用"""
        if not self.offline_config or "models" not in self.offline_config:
            return False, "配置文件中未找到模型配置"
            
        missing_models = []
        for model_name, model_path in self.offline_config["models"].items():
            if not os.path.exists(model_path):
                missing_models.append(f"{model_name}: {model_path}")
                
        if missing_models:
            return False, f"缺少模型文件:\n" + "\n".join(missing_models)
            
        return True, "所有模型文件已就绪"
    
    def initialize_ocr(self):
        """初始化OCR引擎 - 使用外部模型"""
        try:
            # 首先检查模型是否可用
            models_available, message = self.check_models_available()
            if not models_available:
                print(f"模型检查失败: {message}")
                return False
            
            if self.offline_config and self.offline_config.get("offline_mode", False):
                # 离线模式
                models = self.offline_config.get("models", {})
                
                if self.precision_mode == '快速':
                    # 快速模式：只使用检测和识别模型
                    params = {
                        "use_textline_orientation": False,  # 新API参数名
                        "lang": "ch"
                        # 移除不支持的 use_gpu 参数
                    }
                    
                    if "det_model_dir" in models and os.path.exists(models["det_model_dir"]):
                        params["det_model_dir"] = models["det_model_dir"]
                        print(f"使用检测模型: {models['det_model_dir']}")
                    
                    if "rec_model_dir" in models and os.path.exists(models["rec_model_dir"]):
                        params["rec_model_dir"] = models["rec_model_dir"]
                        print(f"使用识别模型: {models['rec_model_dir']}")
                
                else:
                    # 高精度模式：使用所有可用模型
                    params = {
                        "use_textline_orientation": True,  # 新API参数名
                        "lang": "ch"
                        # 移除不支持的 use_gpu 参数
                    }
                    
                    if "det_model_dir" in models and os.path.exists(models["det_model_dir"]):
                        params["det_model_dir"] = models["det_model_dir"]
                    
                    if "rec_model_dir" in models and os.path.exists(models["rec_model_dir"]):
                        params["rec_model_dir"] = models["rec_model_dir"]
                        
                    if "cls_model_dir" in models and os.path.exists(models["cls_model_dir"]):
                        params["cls_model_dir"] = models["cls_model_dir"]
                
                print(f"初始化离线OCR引擎 - 模式: {self.precision_mode}")
                print(f"OCR参数: {params}")
                
                # 延迟导入PaddleOCR，避免启动时模块加载问题
                try:
                    print("正在导入PaddleOCR...")
                    # 设置环境变量，解决exe环境下可能的库冲突
                    # import os  # os已经在文件顶部导入了，不需要重复导入
                    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
                    
                    from paddleocr import PaddleOCR
                    print("PaddleOCR导入成功，正在初始化...")
                    self.ocr_engine = PaddleOCR(**params)
                    print("SUCCESS: 离线OCR引擎初始化成功")
                    return True
                except ImportError as e:
                    print(f"ERROR: PaddleOCR导入失败: {e}")
                    print("可能的原因:")
                    print("1. PaddleOCR未正确打包到exe中")
                    print("2. 缺少相关依赖库")
                    return False
                except Exception as e:
                    print(f"ERROR: PaddleOCR初始化失败: {e}")
                    print(f"错误类型: {type(e).__name__}")
                    print("详细错误信息:")
                    import traceback
                    traceback.print_exc()
                    print("可能的原因:")
                    print("1. 模型文件路径问题")
                    print("2. 模型文件损坏")
                    print("3. 内存不足") 
                    print("4. PaddleOCR版本兼容性问题")
                    return False
            else:
                print("ERROR: 未找到有效的离线配置")
                return False
                
        except Exception as e:
            print(f"ERROR: OCR引擎初始化失败: {e}")
            return False
    
    def set_precision_mode(self, mode):
        """设置精度模式"""
        if mode in ['快速', '高精']:
            self.precision_mode = mode
            # 需要重新初始化引擎
            self.ocr_engine = None
            print(f"精度模式设置为: {mode}")
            return True
        else:
            print("无效的精度模式，支持的模式: '快速', '高精'")
            return False
    
    def run_ocr(self, image_path):
        """执行OCR识别"""
        # 确保OCR引擎已初始化
        if self.ocr_engine is None:
            if not self.initialize_ocr():
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
            
            # 执行OCR识别
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
                    print(f"使用新格式提取文本，共{len(texts)}条")
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
                    print(f"使用旧格式提取文本，共{len(texts)}条")
        except (IndexError, TypeError) as e:
            print(f"文本提取出错: {e}")
        return texts
    
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
        
        try:
            # 提取发票号码
            number_patterns = [
                r'发票号码[：:]\s*([0-9]{6,20})',
                r'发票号[：:]?\s*([0-9]{6,20})',
                r'号码[：:]\s*([0-9]{6,20})',
                r'No[：:.]?\s*([0-9]{6,20})',
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
            # 提取发票金额 - 优化金额提取逻辑
            amount_patterns = [
                r'价税合计[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)',  # 价税合计：123.45
                r'价税合计[：:][^￥¥\d]*([0-9]+\.?[0-9]*)\s*[￥¥]?',  # 价税合计：￥123.45
                r'合计[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)',     # 合计：123.45
                r'小写[：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)',     # 小写：123.45
                r'金额[（\(]不含税[）\)][：:][^￥¥\d]*[￥¥]?\s*([0-9]+\.?[0-9]*)', # 金额（不含税）：123.45
                r'[￥¥]\s*([0-9]+\.?[0-9]*)',  # ￥123.45
            ]
            
            for pattern in amount_patterns:
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
                        invoice_amount = max(valid_amounts)  # 通常取最大的金额作为发票总额
                        print(f"提取到发票金额: {invoice_amount}")
                        break
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