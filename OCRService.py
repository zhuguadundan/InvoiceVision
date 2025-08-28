#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR服务 - 独立的发票OCR识别服务
负责图像识别和文本提取，通过JSON通信提供服务
"""

import json
import sys
import uuid
import os
import threading
import time
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import re

class OCRService:
    def __init__(self):
        self.reader = None
        self.initialize_ocr()
        
    def initialize_ocr(self):
        """初始化EasyOCR引擎"""
        try:
            import easyocr
            self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
            self.log("[SUCCESS] OCR服务初始化成功")
        except Exception as e:
            self.log(f"[ERROR] OCR服务初始化失败: {e}")
            sys.exit(1)
    
    def log(self, message):
        """日志输出到stderr，避免与stdin/stdout通信冲突"""
        print(f"[OCRService] {message}", file=sys.stderr, flush=True)
    
    def process_request(self, request_data):
        """处理OCR识别请求"""
        try:
            request_id = request_data.get('request_id', str(uuid.uuid4()))
            action = request_data.get('action')
            
            if action == 'ocr_recognize':
                return self._handle_ocr_recognize(request_data, request_id)
            elif action == 'health_check':
                return {
                    "request_id": request_id,
                    "status": "success", 
                    "result": {"service": "ready", "ocr_engine": "EasyOCR"},
                    "error": None
                }
            else:
                return {
                    "request_id": request_id,
                    "status": "error",
                    "result": None,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            return {
                "request_id": request_data.get('request_id', 'unknown'),
                "status": "error",
                "result": None,
                "error": str(e)
            }
    
    def _handle_ocr_recognize(self, request_data, request_id):
        """处理OCR识别请求"""
        image_path = request_data.get('image_path')
        precision_mode = request_data.get('precision_mode', '快速')
        
        if not image_path or not os.path.exists(image_path):
            return {
                "request_id": request_id,
                "status": "error",
                "result": None,
                "error": f"Image file not found: {image_path}"
            }
        
        try:
            # 执行OCR识别
            invoice_info = self._run_ocr(image_path, precision_mode)
            
            return {
                "request_id": request_id,
                "status": "success",
                "result": {
                    "image_path": image_path,
                    "invoice_code": invoice_info[1],
                    "invoice_number": invoice_info[2], 
                    "date": invoice_info[3],
                    "amount": invoice_info[4],
                    "company": invoice_info[5] if len(invoice_info) > 5 else ""
                },
                "error": None
            }
            
        except Exception as e:
            self.log(f"OCR识别出错: {e}")
            return {
                "request_id": request_id,
                "status": "error", 
                "result": None,
                "error": str(e)
            }
    
    def _run_ocr(self, image_path, precision_mode='快速'):
        """执行OCR识别 - 复用原有OCRInvoice逻辑"""
        try:
            self.log(f"开始处理图片: {os.path.basename(image_path)}")
            
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
                pil_image = Image.open(image_path)
                img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # 执行OCR识别
            result = self.reader.readtext(img)
            texts = self._extract_texts_from_easyocr_result(result)
            
            if not texts:
                self.log("OCR未识别到任何文本")
                return [image_path, '', '', '', '']
            
            # 检查是否识别到发票内容
            combined_text = '【' + '】【'.join(texts) + '】'
            
            if not self._contains_invoice_keywords(combined_text):
                self.log("未检测到发票关键词，尝试旋转图片...")
                img_rotated = cv2.rotate(img, cv2.ROTATE_180)
                result = self.reader.readtext(img_rotated)
                texts = self._extract_texts_from_easyocr_result(result)
                combined_text = '【' + '】【'.join(texts) + '】'
            
            # 提取发票信息
            invoice_info = self._extract_invoice_info(combined_text, image_path)
            self.log(f"识别完成: {os.path.basename(image_path)}")
            return invoice_info
            
        except Exception as e:
            self.log(f"OCR处理出错: {e}")
            return [image_path, '', '', '', '']
    
    def _extract_texts_from_easyocr_result(self, result):
        """从EasyOCR结果中提取文本"""
        texts = []
        try:
            for detection in result:
                if len(detection) >= 2:
                    text = detection[1].strip()
                    if text:
                        texts.append(text)
            
            self.log(f"EasyOCR识别到{len(texts)}条文本")
            return texts
            
        except Exception as e:
            self.log(f"EasyOCR文本提取出错: {e}")
            return []
    
    def _contains_invoice_keywords(self, text):
        """检查文本是否包含发票关键词"""
        keywords = ['发票', '增值税', '专用发票', '普通发票', '发票号码', '发票代码']
        return any(keyword in text for keyword in keywords)
    
    def _extract_invoice_info(self, combined_text, image_path):
        """从识别文本中提取发票信息 - 复用原有正则表达式逻辑"""
        try:
            # 发票代码 (通常是10-12位数字)
            invoice_code_pattern = r'发票代码[：:\s]*(\d{10,12})'
            invoice_code_match = re.search(invoice_code_pattern, combined_text)
            invoice_code = invoice_code_match.group(1) if invoice_code_match else ''
            
            # 发票号码 (通常是8位数字)
            invoice_number_pattern = r'发票号码[：:\s]*(\d{8})'
            invoice_number_match = re.search(invoice_number_pattern, combined_text)
            invoice_number = invoice_number_match.group(1) if invoice_number_match else ''
            
            # 开票日期 (YYYYMMDD格式)
            date_pattern = r'(\d{4}年\d{1,2}月\d{1,2}日|\d{8})'
            date_match = re.search(date_pattern, combined_text)
            date = date_match.group(1) if date_match else ''
            
            # 金额(不含税)
            amount_pattern = r'[金￥¥]额[^税]*?(\d+\.?\d*)'
            amount_match = re.search(amount_pattern, combined_text)
            amount = amount_match.group(1) if amount_match else ''
            
            # 公司名称 (发票抬头)
            company_pattern = r'购买方[名称]*[：:\s]*([^纳税人]*?)(?=纳税人识别号|$)'
            company_match = re.search(company_pattern, combined_text)
            company = company_match.group(1).strip() if company_match else ''
            
            return [image_path, invoice_code, invoice_number, date, amount, company]
            
        except Exception as e:
            self.log(f"发票信息提取出错: {e}")
            return [image_path, '', '', '', '']
    
    def run_service(self):
        """运行服务主循环"""
        self.log("OCR服务启动，等待请求...")
        
        try:
            while True:
                # 从stdin读取请求
                try:
                    line = sys.stdin.readline().strip()
                    if not line:
                        continue
                        
                    # 解析JSON请求
                    request_data = json.loads(line)
                    
                    # 处理请求
                    response = self.process_request(request_data)
                    
                    # 输出响应到stdout
                    print(json.dumps(response, ensure_ascii=False), flush=True)
                    
                except json.JSONDecodeError as e:
                    error_response = {
                        "request_id": "unknown",
                        "status": "error",
                        "result": None,
                        "error": f"Invalid JSON request: {e}"
                    }
                    print(json.dumps(error_response, ensure_ascii=False), flush=True)
                    
                except KeyboardInterrupt:
                    self.log("接收到中断信号，服务退出")
                    break
                    
        except Exception as e:
            self.log(f"服务运行异常: {e}")
            sys.exit(1)

if __name__ == "__main__":
    try:
        service = OCRService()
        service.run_service()
    except Exception as e:
        print(f"[ERROR] 服务启动失败: {e}", file=sys.stderr)
        sys.exit(1)