#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller hook for jaraco modules
确保所有 jaraco 相关模块都被正确包含
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 收集所有 jaraco 相关模块
hiddenimports = []

try:
    # 自动收集所有 jaraco 子模块
    jaraco_submodules = collect_submodules('jaraco')
    hiddenimports.extend(jaraco_submodules)
    
    # 手动添加常用的 jaraco 模块（确保包含）
    essential_jaraco_modules = [
        'jaraco.text',
        'jaraco.functools',
        'jaraco.context',
        'jaraco.collections',
        'jaraco.itertools',
        'jaraco.classes',
    ]
    
    for module in essential_jaraco_modules:
        if module not in hiddenimports:
            hiddenimports.append(module)
            
except ImportError:
    # 如果 jaraco 不可用，至少包含核心模块
    hiddenimports = [
        'jaraco',
        'jaraco.text', 
        'jaraco.functools',
        'jaraco.context',
    ]

# 收集数据文件
datas = []
try:
    jaraco_data = collect_data_files('jaraco')
    datas.extend(jaraco_data)
except ImportError:
    pass