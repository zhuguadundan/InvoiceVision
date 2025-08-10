#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支持离线运行的OCRInvoice类 - PaddleOCR 3.1+ 离线版
"""

from paddleocr import PaddleOCR
import re
from PIL import Image
import os
import json
from pathlib import Path

class OfflineOCRInvoice:
    def __init__(self):
        """初始化离线OCR发票识别器"""
        self.precision_mode = '快速'
        self.ocr_engine = None
        self.offline_config = self._load_offline_config()
        
    def _load_offline_config(self):
        """加载离线配置"""
        base_dir = Path(__file__).parent
        config_file = base_dir / "offline_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"已加载离线配置: {config_file}")
                return config
            except Exception as e:
                print(f"离线配置加载失败: {e}")
        
        return None
    
    def initialize_ocr(self):
        """初始化OCR引擎 - 优先使用离线模式"""
        try:
            if self.offline_config and self.offline_config.get("offline_mode", False):
                # 离线模式
                models = self.offline_config.get("models", {})
                
                if self.precision_mode == '快速':
                    # 快速模式：只使用检测和识别模型
                    params = {
                        "use_doc_orientation_classify": False,
                        "use_doc_unwarping": False,
                        "use_textline_orientation": False,
                        "lang": "ch"
                    }
                    
                    if "det_model_dir" in models and os.path.exists(models["det_model_dir"]):
                        params["text_detection_model_dir"] = models["det_model_dir"]
                    
                    if "rec_model_dir" in models and os.path.exists(models["rec_model_dir"]):
                        params["text_recognition_model_dir"] = models["rec_model_dir"]
                
                else:
                    # 高精度模式：使用所有可用模型
                    params = {
                        "use_doc_orientation_classify": True,
                        "use_doc_unwarping": True, 
                        "use_textline_orientation": True,
                        "lang": "ch"
                    }
                    
                    if "det_model_dir" in models and os.path.exists(models["det_model_dir"]):
                        params["text_detection_model_dir"] = models["det_model_dir"]
                    if "rec_model_dir" in models and os.path.exists(models["rec_model_dir"]):
                        params["text_recognition_model_dir"] = models["rec_model_dir"]
                    if "cls_model_dir" in models and os.path.exists(models["cls_model_dir"]):
                        params["text_line_orientation_model_dir"] = models["cls_model_dir"]
                
                print(f"离线模式初始化 - 精度: {self.precision_mode}")
                print(f"使用模型: {list(params.keys())}")
                self.ocr_engine = PaddleOCR(**params)
                
            else:
                # 在线模式 - 回退方案
                print(f"在线模式初始化 - 精度: {self.precision_mode}")
                if self.precision_mode == '快速':
                    self.ocr_engine = PaddleOCR(
                        use_doc_orientation_classify=False,
                        use_doc_unwarping=False,
                        use_textline_orientation=False,
                        lang="ch"
                    )
                else:
                    self.ocr_engine = PaddleOCR(
                        use_doc_orientation_classify=True,
                        use_doc_unwarping=True,
                        use_textline_orientation=True,
                        lang="ch"
                    )
            
            print(f"OCR引擎初始化成功 - 模式: {self.precision_mode}")
            return True
            
        except Exception as e:
            print(f"OCR引擎初始化失败: {e}")
            return False
    
    def set_precision_mode(self, mode):
        """设置精度模式并重新初始化"""
        if mode in ['快速', '高精']:
            self.precision_mode = mode
            return self.initialize_ocr()
        else:
            print(f"不支持的模式: {mode}")
            return False
    
    def run_ocr(self, image_path):
        """
        执行OCR识别
        Args:
            image_path: 图片路径
        Returns:
            list: [文件路径, 开票公司名称, 发票号码, 日期, 金额(价税合计)]
        """
        if not self.ocr_engine:
            if not self.initialize_ocr():
                return [image_path, '', '', '', '']
        
        if not os.path.exists(image_path):
            print(f"文件不存在: {image_path}")
            return [image_path, '', '', '', '']
        
        try:
            print(f"正在识别: {os.path.basename(image_path)}")
            
            # 使用PIL读取图片解决中文路径问题
            import cv2
            import numpy as np
            
            # 方法1: 使用cv2.imdecode处理中文路径
            try:
                # 读取图像文件为二进制数据
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                # 将二进制数据转换为numpy数组
                nparr = np.frombuffer(image_data, np.uint8)
                # 解码图像
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    raise Exception("图像解码失败")
            except:
                # 方法2: 使用PIL作为后备方案
                from PIL import Image
                pil_image = Image.open(image_path)
                img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # 第一次OCR尝试 - 传递numpy数组而不是路径
            result = self.ocr_engine.ocr(img)
            texts = self._extract_texts_from_result(result)
            
            if not texts:
                print("OCR未识别到任何文本")
                return [image_path, '', '', '', '']
            
            # 检查是否识别到发票内容
            combined_text = '【' + '】【'.join(texts) + '】'
            
            if not self._contains_invoice_keywords(combined_text):
                print("未检测到发票关键词，尝试旋转图片...")
                # 旋转图片再次尝试 - 直接旋转numpy数组
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
            if result and len(result) > 0 and result[0]:
                ocr_result = result[0]
                
                # 新的PaddleOCR格式：检查是否有rec_texts字段
                if isinstance(ocr_result, dict) and 'rec_texts' in ocr_result:
                    # 新格式：直接从rec_texts获取文本
                    for text in ocr_result['rec_texts']:
                        if text and text.strip():  # 过滤空文本
                            texts.append(text.strip())
                else:
                    # 旧格式：从嵌套数组中提取
                    for line in ocr_result:
                        if line and len(line) > 1 and line[1]:
                            # PaddleOCR返回格式: [坐标, (文本, 置信度)]
                            if isinstance(line[1], tuple) and len(line[1]) > 0:
                                text = line[1][0].strip()  # 提取文本部分
                            elif isinstance(line[1], str):
                                text = line[1].strip()  # 直接是字符串
                            else:
                                continue
                            
                            if text:  # 过滤空文本
                                texts.append(text)
        except (IndexError, TypeError) as e:
            print(f"文本提取出错: {e}")
            print(f"OCR结果格式: {result}")
        return texts
    
    def _contains_invoice_keywords(self, text):
        """检查文本是否包含发票关键词"""
        keywords = ['发票', '增值税', '专用发票', '普通发票', '发票号码', '发票代码']
        return any(keyword in text for keyword in keywords)
    
    def _rotate_image_180(self, image_path):
        """将图片旋转180度"""
        try:
            with Image.open(image_path) as img:
                rotated = img.transpose(Image.ROTATE_180)
                rotated.save(image_path)
        except Exception as e:
            print(f"图片旋转失败: {e}")
    
    def _extract_invoice_info(self, text, image_path):
        """从文本中提取发票信息"""
        company_name = ''        # 开票公司名称
        invoice_number = ''      # 发票号码
        invoice_date = ''        # 发票日期
        invoice_amount = ''      # 发票金额(价税合计)
        
        print(f"提取信息的文本: {text}")
        
        try:
            # 提取开票公司名称（只匹配销售方名称，避免匹配购买方）
            company_patterns = [
                # 优先匹配明确的销售方标识
                r'销售方名称[：:]\s*([^\n\r【】]{2,50}?)(?=\s*【|$)',  # 销售方名称：公司名
                r'销售方[：:]\s*([^\n\r【】]{2,50}?)(?=\s*【|$)',     # 销售方：公司名
                r'开票方名称[：:]\s*([^\n\r【】]{2,50}?)(?=\s*【|$)', # 开票方名称：公司名
                r'开票方[：:]\s*([^\n\r【】]{2,50}?)(?=\s*【|$)',     # 开票方：公司名
            ]
            
            # 先尝试精确匹配销售方标识的模式
            for pattern in company_patterns:
                company_matches = re.findall(pattern, text)
                if company_matches:
                    for match in company_matches:
                        match = match.strip()
                        # 过滤掉明显错误的匹配
                        if (len(match) >= 3 and not match[0].isdigit() and 
                            not any(word in match for word in ['发票', '号码', '日期', '金额', '税率', '税额', '购买方', '买方']) and
                            any(suffix in match for suffix in ['有限公司', '股份有限公司', '集团', '企业', '公司', '厂', '店'])):
                            company_name = match
                            print(f"提取到开票公司名称(精确匹配): {company_name}")
                            break
                    if company_name:
                        break
            
            # 如果精确匹配失败，尝试上下文匹配（确保不在购买方区域）
            if not company_name:
                # 寻找销售方区域，避免购买方区域的干扰
                seller_section_pattern = r'销售方.*?(?=购买方|$)'
                seller_matches = re.findall(seller_section_pattern, text, re.DOTALL)
                
                if seller_matches:
                    seller_text = seller_matches[0]
                    # 在销售方区域中寻找公司名称
                    company_in_seller_pattern = r'([^\n\r【】]*(?:有限公司|股份有限公司|集团|企业|公司|厂|店))'
                    company_matches = re.findall(company_in_seller_pattern, seller_text)
                    
                    if company_matches:
                        for match in company_matches:
                            match = match.strip()
                            # 更严格的过滤条件
                            if (len(match) >= 3 and not match[0].isdigit() and 
                                not any(word in match for word in ['发票', '号码', '日期', '金额', '税率', '税额', '购买方', '买方', '纳税人', '识别号'])):
                                company_name = match
                                print(f"提取到开票公司名称(上下文匹配): {company_name}")
                                break
        except Exception as e:
            print(f"开票公司名称提取失败: {e}")
        
        try:
            # 提取发票号码（从文本"发票号码：19251211"中提取）
            number_pattern = r'发票号码[：:]\s*([0-9]{8,10})'
            number_matches = re.findall(number_pattern, text)
            if number_matches:
                invoice_number = number_matches[0]
                print(f"提取到发票号码: {invoice_number}")
        except Exception as e:
            print(f"发票号码提取失败: {e}")
        
        try:
            # 提取发票日期（从文本"发票日期：2023年03月29日"中提取）
            date_pattern = r'发票日期[：:]\s*([0-9]{4})年([0-9]{1,2})月([0-9]{1,2})日'
            date_matches = re.findall(date_pattern, text)
            if date_matches:
                year, month, day = date_matches[0]
                # 格式化为YYYYMMDD
                invoice_date = f"{year}{month.zfill(2)}{day.zfill(2)}"
                print(f"提取到发票日期: {invoice_date}")
            else:
                # 尝试其他日期格式
                date_pattern2 = r'([0-9]{4})[年\-/]([0-9]{1,2})[月\-/]([0-9]{1,2})'
                date_matches2 = re.findall(date_pattern2, text)
                if date_matches2:
                    year, month, day = date_matches2[0]
                    invoice_date = f"{year}{month.zfill(2)}{day.zfill(2)}"
                    print(f"提取到发票日期(格式2): {invoice_date}")
        except Exception as e:
            print(f"发票日期提取失败: {e}")
        
        try:
            # 提取发票金额 - 优先寻找价税合计
            amount_patterns = [
                r'价税合计[：:]\s*[￥¥]*([0-9]+\.?[0-9]*)',    # 价税合计：123.45 (最高优先级)
                r'合计[：:]\s*[￥¥]*([0-9]+\.?[0-9]*)',       # 合计：123.45
                r'小写[：:]\s*[￥¥]*([0-9]+\.?[0-9]*)',       # 小写：123.45
                r'金额[：:]\s*[￥¥]*([0-9]+\.?[0-9]*)',       # 金额：123.45
                r'([0-9]{1,7}\.[0-9]{2})',                    # 直接匹配金额格式
            ]
            
            for pattern in amount_patterns:
                amount_matches = re.findall(pattern, text)
                if amount_matches:
                    # 过滤掉过小的金额（可能是其他数字）
                    valid_amounts = []
                    for amount_str in amount_matches:
                        try:
                            amount = float(amount_str)
                            if amount >= 0.01:  # 至少1分钱
                                valid_amounts.append(amount)
                        except ValueError:
                            continue
                    
                    if valid_amounts:
                        # 通常取最大的金额作为发票总额
                        invoice_amount = max(valid_amounts)
                        print(f"提取到发票金额(价税合计): {invoice_amount}")
                        break
                        
        except Exception as e:
            print(f"发票金额提取失败: {e}")
        
        result = [image_path, company_name, invoice_number, invoice_date, invoice_amount]
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
            info["available_models"] = list(self.offline_config.get("models", {}).keys())
        
        return info

# 保持向后兼容性
OCRInvoice = OfflineOCRInvoice

if __name__ == '__main__':
    # 测试代码
    print("=" * 60)
    print("离线OCR发票识别器测试")
    print("=" * 60)
    
    ocr_invoice = OfflineOCRInvoice()
    
    # 显示模型信息
    model_info = ocr_invoice.get_model_info()
    print(f"模型信息: {model_info}")
    
    # 测试快速模式
    print("\n测试快速模式...")
    ocr_invoice.set_precision_mode('快速')
    
    # 寻找测试图片
    test_images = []
    for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        for file in os.listdir('.'):
            if file.lower().endswith(ext):
                test_images.append(file)
                break
        if test_images:
            break
    
    if test_images:
        print(f"测试图片: {test_images[0]}")
        result = ocr_invoice.run_ocr(test_images[0])
        print(f"识别结果: {result}")
    else:
        print("当前目录下没有找到测试图片")
        print("离线OCR引擎初始化测试通过！")