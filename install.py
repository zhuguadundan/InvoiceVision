#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发票OCR识别器安装脚本
"""

import subprocess
import sys
import os

def install_requirements():
    """安装依赖包"""
    print("=" * 60)
    print("发票OCR识别器 - 依赖安装脚本")
    print("适用于 PaddleOCR 3.1+ / PP-OCRv5")
    print("=" * 60)
    
    try:
        # 检查pip
        print("检查pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
        
        # 升级pip
        print("\n升级pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # 安装依赖
        print("\n安装项目依赖...")
        if os.path.exists("requirements.txt"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        else:
            # 手动安装核心依赖
            packages = [
                "paddleocr>=3.1.0",
                "paddlepaddle>=3.0.0", 
                "pillow>=8.0.0",
                "pandas>=1.3.0",
                "pyqt5>=5.15.0",
                "pymupdf>=1.20.0"
            ]
            
            for package in packages:
                print(f"安装 {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        print("\n" + "=" * 60)
        print("✅ 依赖安装完成！")
        print("✅ 现在可以运行程序了：")
        print("   python InvoiceVision.py")
        print("=" * 60)
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 安装失败: {e}")
        print("请检查网络连接或手动安装依赖")
        return False
    except Exception as e:
        print(f"\n❌ 出现错误: {e}")
        return False
    
    return True

def check_installation():
    """检查安装是否成功"""
    print("\n检查安装状态...")
    
    try:
        import paddleocr
        print(f"✅ PaddleOCR 版本: {paddleocr.__version__}")
        
        import pandas
        print(f"✅ Pandas 版本: {pandas.__version__}")
        
        from PyQt5 import QtCore
        print(f"✅ PyQt5 版本: {QtCore.PYQT_VERSION_STR}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

if __name__ == "__main__":
    if install_requirements():
        check_installation()
    
    input("\n按回车键退出...")