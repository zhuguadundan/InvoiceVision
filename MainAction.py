#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线版主要操作模块 - 支持完全离线运行
"""

from OCRInvoice import OfflineOCRInvoice
from PDF2IMG import pdf2img
from pandas import DataFrame
from os import listdir
import os

def ocr_pdf_offline(pdf_path, precision_mode, output_dir=None):
    """
    离线处理PDF文件中的发票
    Args:
        pdf_path: PDF文件路径
        precision_mode: 精度模式 ('快速' 或 '高精')
        output_dir: 输出目录（可选）
    Returns:
        dict: 包含识别结果的字典
    """
    try:
        print(f"开始处理PDF: {pdf_path}")
        print(f"精度模式: {precision_mode}")
        
        # 创建结果DataFrame
        invoice_info = DataFrame(columns=['文件地址', '开票公司', '发票号码', '日期', '金额（价税合计）', '项目名称'])
        
        # 转换PDF为图片
        print("正在将PDF转换为图片...")
        pdf_converter = pdf2img()
        pdf_converter.pyMuPDF_fitz(pdf_path, output_dir=output_dir)
        print(f"PDF转换完成，图片保存路径: {pdf_converter.imagePath}")
        
        # 初始化离线OCR识别器 - 使用全局预初始化的引擎
        print("创建OCR引擎实例...")
        ocr_engine = OfflineOCRInvoice()
        
        # 检查全局OCR引擎状态
        if ocr_engine.ocr_engine is None:
            print("ERROR: 全局OCR引擎未初始化，请确保应用启动时已完成预初始化")
            return
        
        print(f"✅ 使用全局OCR引擎，模式: {precision_mode}")
        
        # 显示模型信息
        model_info = ocr_engine.get_model_info()
        print(f"OCR模型信息: {model_info}")
        
        # 处理所有转换后的图片
        item_no = 1
        processed_count = 0
        
        # 确保在路径不存在时变量可用，避免 NameError
        image_files = []
        
        if os.path.exists(pdf_converter.imagePath):
            image_files = [f for f in listdir(pdf_converter.imagePath) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
            
            print(f"找到 {len(image_files)} 个图片文件")
            
            for filename in image_files:
                print(f"[{item_no}/{len(image_files)}] 正在处理: {filename}")
                image_path = os.path.join(pdf_converter.imagePath, filename)
                
                # 执行OCR识别
                result = ocr_engine.run_ocr(image_path)
                # 确保结果有正确的长度（6个字段：文件路径, 公司名称, 发票号码, 日期, 金额, 项目名称）
                while len(result) < 6:
                    result.append('')  # 补充空字段
                if len(result) > 6:
                    result = result[:6]  # 截断多余字段
                invoice_info.loc[item_no] = result
                
                # 显示识别结果
                if result[1] or result[2]:  # 如果识别到公司名称或发票号码
                    processed_count += 1
                    print(f"  识别成功: 公司={result[1]}, 号码={result[2]}")
                else:
                    print(f"  未识别到发票信息")
                
                item_no += 1
        
        print(f"\n处理完成！")
        print(f"总计处理: {len(image_files)} 个文件")
        print(f"成功识别: {processed_count} 个发票")
        print(f"识别率: {processed_count/len(image_files)*100:.1f}%" if image_files else "N/A")
        
        # 显示结果预览
        print("\n识别结果预览:")
        print(invoice_info.to_string(index=False, max_rows=10))
        
        # 返回结果数据供界面显示 - 修改为兼容新GUI的格式
        invoice_list = []
        if not invoice_info.empty:
            # 将DataFrame转换为列表格式
            for _, row in invoice_info.iterrows():
                invoice_list.append([
                    row['文件地址'],     # 文件路径
                    row['开票公司'],     # 开票公司名称
                    row['发票号码'],     # 发票号码
                    row['日期'],        # 发票日期
                    row['金额（价税合计）'], # 发票金额
                    row['项目名称']      # 项目名称
                ])
        
        result_data = {
            "total_files": len(image_files) if 'image_files' in locals() else 0,
            "processed_count": processed_count,
            "success_rate": f"{processed_count/len(image_files)*100:.1f}%" if 'image_files' in locals() and image_files else "0%",
            "invoice_data": invoice_list  # 新的格式，直接是列表
        }
        
        return result_data
        
    except Exception as e:
        print(f"PDF处理出错: {e}")
        import traceback
        traceback.print_exc()

def ocr_images_offline(image_folder_path, precision_mode, output_dir=None):
    """
    离线处理图片文件夹中的发票
    Args:
        image_folder_path: 图片文件夹路径
        precision_mode: 精度模式 ('快速' 或 '高精')
        output_dir: 输出目录（可选）
    Returns:
        dict: 包含识别结果的字典
    """
    try:
        print(f"开始处理图片文件夹: {image_folder_path}")
        print(f"精度模式: {precision_mode}")
        
        # 创建结果DataFrame
        invoice_info = DataFrame(columns=['文件地址', '开票公司', '发票号码', '日期', '金额（价税合计）', '项目名称'])
        
        # 初始化离线OCR识别器 - 使用全局预初始化的引擎
        print("创建OCR引擎实例...")
        ocr_engine = OfflineOCRInvoice()
        
        # 检查全局OCR引擎状态
        if ocr_engine.ocr_engine is None:
            print("ERROR: 全局OCR引擎未初始化，请确保应用启动时已完成预初始化")
            return
        
        print(f"✅ 使用全局OCR引擎，模式: {precision_mode}")
        
        # 显示模型信息
        model_info = ocr_engine.get_model_info()
        print(f"OCR模型信息: {model_info}")
        
        # 处理文件夹中的所有图片
        item_no = 1
        processed_count = 0
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
        
        # 确保在路径不存在时变量可用，避免 NameError
        image_files = []
        
        if os.path.exists(image_folder_path):
            image_files = [f for f in listdir(image_folder_path) 
                          if f.lower().endswith(supported_formats)]
            
            print(f"找到 {len(image_files)} 个图片文件")
            
            for filename in image_files:
                print(f"[{item_no}/{len(image_files)}] 正在处理: {filename}")
                image_path = os.path.join(image_folder_path, filename)
                
                # 执行OCR识别
                result = ocr_engine.run_ocr(image_path)
                # 确保结果有正确的长度（6个字段：文件路径, 公司名称, 发票号码, 日期, 金额, 项目名称）
                while len(result) < 6:
                    result.append('')  # 补充空字段
                if len(result) > 6:
                    result = result[:6]  # 截断多余字段
                invoice_info.loc[item_no] = result
                
                # 显示识别结果
                if result[1] or result[2]:  # 如果识别到公司名称或发票号码
                    processed_count += 1
                    print(f"  识别成功: 公司={result[1]}, 号码={result[2]}")
                else:
                    print(f"  未识别到发票信息")
                
                item_no += 1
        
        print(f"\n处理完成！")
        print(f"总计处理: {len(image_files)} 个文件")
        print(f"成功识别: {processed_count} 个发票")
        print(f"识别率: {processed_count/len(image_files)*100:.1f}%" if image_files else "N/A")
        
        # 显示结果预览
        print("\n识别结果预览:")
        print(invoice_info.to_string(index=False, max_rows=10))
        
        # 返回结果数据供界面显示 - 修改为兼容新GUI的格式
        invoice_list = []
        if not invoice_info.empty:
            # 将DataFrame转换为列表格式
            for _, row in invoice_info.iterrows():
                invoice_list.append([
                    row['文件地址'],     # 文件路径
                    row['开票公司'],     # 开票公司名称
                    row['发票号码'],     # 发票号码
                    row['日期'],        # 发票日期
                    row['金额（价税合计）'], # 发票金额
                    row['项目名称']      # 项目名称
                ])
        
        result_data = {
            "total_files": len(image_files) if 'image_files' in locals() else 0,
            "processed_count": processed_count,
            "success_rate": f"{processed_count/len(image_files)*100:.1f}%" if 'image_files' in locals() and image_files else "0%",
            "invoice_data": invoice_list  # 新的格式，直接是列表
        }
        
        return result_data
        
    except Exception as e:
        print(f"图片处理出错: {e}")
        import traceback
        traceback.print_exc()

# 保持向后兼容性
def OCR_PDF(pdf_path, flag):
    """向后兼容的PDF处理函数"""
    return ocr_pdf_offline(pdf_path, flag)

def OCR_IMGS(img_path, flag):
    """向后兼容的图片处理函数"""  
    return ocr_images_offline(img_path, flag)

## 注意：正式应用通过 GUI 启动；原本的直跑测试代码已移除以降低噪音。
