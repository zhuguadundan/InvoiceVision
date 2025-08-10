#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发票信息提取
"""

import os
from OCRInvoice import OfflineOCRInvoice

def test_extraction():
    """测试发票信息提取"""
    
    # 初始化OCR引擎
    ocr = OfflineOCRInvoice()
    
    # 查找测试图片
    img_dir = "IMG/033002200511_19251211_金华市妇幼保健院"
    if os.path.exists(img_dir):
        image_files = [f for f in os.listdir(img_dir) if f.endswith('.png')]
        
        if image_files:
            test_image = os.path.join(img_dir, image_files[0])
            print(f"测试图片: {test_image}")
            
            # 运行完整OCR流程
            result = ocr.run_ocr(test_image)
            print(f"\n完整OCR结果: {result}")
            
            # 解析结果
            if len(result) >= 5:
                print(f"\n解析结果:")
                print(f"文件路径: {result[0]}")
                print(f"发票代码: {result[1]}")
                print(f"发票号码: {result[2]}")
                print(f"发票日期: {result[3]}")
                print(f"发票金额: {result[4]}")
        else:
            print("未找到测试图片")
    else:
        print(f"目录不存在: {img_dir}")

if __name__ == "__main__":
    test_extraction()