#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支持打包的资源路径管理器
"""

import os
import sys
from pathlib import Path

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持PyInstaller打包环境"""
    try:
        # PyInstaller创建临时文件夹并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_models_path():
    """获取模型文件夹路径"""
    return get_resource_path("models")

def get_config_path():
    """获取配置文件路径"""
    return get_resource_path("offline_config.json")

def init_models_config():
    """初始化模型配置，适配打包环境"""
    models_path = get_models_path()
    
    config = {
        "offline_mode": True,
        "models": {
            "cls_model_dir": os.path.join(models_path, "PP-LCNet_x1_0_textline_ori"),
            "det_model_dir": os.path.join(models_path, "PP-OCRv5_server_det"),
            "rec_model_dir": os.path.join(models_path, "PP-OCRv5_server_rec")
        },
        "use_gpu": False,
        "lang": "ch"
    }
    
    return config