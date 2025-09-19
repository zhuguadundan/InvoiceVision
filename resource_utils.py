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
    """获取模型文件夹路径 - 支持外部模型架构"""
    # 首先检查是否在PyInstaller环境中
    try:
        base_path = sys._MEIPASS
        # 在打包环境中，模型应该位于exe同级目录的models文件夹
        exe_dir = os.path.dirname(sys.executable)
        models_path = os.path.join(exe_dir, "models")
        
        # 如果exe同级目录有models，使用它
        if os.path.exists(models_path):
            return models_path
        else:
            # 否则尝试开发环境的models路径
            return os.path.abspath("models")
    except Exception:
        # 开发环境
        return os.path.abspath("models")

def get_config_path():
    """获取配置文件路径"""
    try:
        # 在打包环境中，配置文件应该位于exe同级目录
        base_path = sys._MEIPASS
        exe_dir = os.path.dirname(sys.executable)
        config_path = os.path.join(exe_dir, "offline_config.json")
        
        # 如果exe同级目录有配置文件，使用它
        if os.path.exists(config_path):
            return config_path
        else:
            # 否则使用开发环境的配置文件
            return get_resource_path("offline_config.json")
    except Exception:
        # 开发环境
        return get_resource_path("offline_config.json")

def init_models_config():
    """初始化模型配置，适配打包环境"""
    models_path = get_models_path()
    
    config = {
        "offline_mode": True,
        "models_path": models_path,
        "models": {
            "det_model_dir": os.path.join(models_path, "PP-OCRv5_mobile_det"),
            "rec_model_dir": os.path.join(models_path, "PP-OCRv5_mobile_rec"),
            "cls_model_dir": os.path.join(models_path, "ch_ppocr_mobile_v2.0_cls")
        },
        "use_gpu": False,
        "lang": "ch",
        "version": "2.1-mobile-default",
        "description": "外部模型架构配置 - 默认使用PP-OCRv5 mobile"
    }
    
    return config
