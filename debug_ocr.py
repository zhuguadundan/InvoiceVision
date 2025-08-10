#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试OCR识别结果
"""

import os
from OCRInvoice import OfflineOCRInvoice

def debug_ocr():
    """调试OCR识别"""
    
    # 初始化OCR引擎
    ocr = OfflineOCRInvoice()
    
    # 查找测试图片
    img_dir = "IMG/033002200511_19251211_金华市妇幼保健院"
    if os.path.exists(img_dir):
        image_files = [f for f in os.listdir(img_dir) if f.endswith('.png')]
        
        if image_files:
            test_image = os.path.join(img_dir, image_files[0])
            print(f"调试图片: {test_image}")
            print(f"文件存在: {os.path.exists(test_image)}")
            
            # 直接调用OCR引擎获取原始结果
            print("\n==== 开始OCR识别 ====")
            if not ocr.ocr_engine:
                if not ocr.initialize_ocr():
                    print("OCR引擎初始化失败")
                    return
            
            # 读取图片
            import cv2
            import numpy as np
            
            try:
                with open(test_image, 'rb') as f:
                    image_data = f.read()
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    print("图像解码失败")
                    return
                
                # 直接调用PaddleOCR
                raw_result = ocr.ocr_engine.ocr(img)
                print(f"原始OCR结果: {raw_result}")
                
                # 提取文本
                texts = ocr._extract_texts_from_result(raw_result)
                print(f"\n提取的文本列表: {texts}")
                
                # 合并文本
                combined_text = '【' + '】【'.join(texts) + '】'
                print(f"\n合并后的文本: {combined_text}")
                
                # 检查关键词
                has_keywords = ocr._contains_invoice_keywords(combined_text)
                print(f"\n包含发票关键词: {has_keywords}")
                
                # 如果没有关键词，尝试旋转
                if not has_keywords:
                    print("\n尝试旋转图片...")
                    img_rotated = cv2.rotate(img, cv2.ROTATE_180)
                    raw_result_rotated = ocr.ocr_engine.ocr(img_rotated)
                    print(f"旋转后的原始OCR结果: {raw_result_rotated}")
                    
                    texts_rotated = ocr._extract_texts_from_result(raw_result_rotated)
                    print(f"旋转后的文本列表: {texts_rotated}")
                    
                    combined_text_rotated = '【' + '】【'.join(texts_rotated) + '】'
                    print(f"旋转后的合并文本: {combined_text_rotated}")
                    
                    has_keywords_rotated = ocr._contains_invoice_keywords(combined_text_rotated)
                    print(f"旋转后包含发票关键词: {has_keywords_rotated}")
                
            except Exception as e:
                print(f"调试过程出错: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("未找到测试图片")
    else:
        print(f"目录不存在: {img_dir}")

if __name__ == "__main__":
    debug_ocr()