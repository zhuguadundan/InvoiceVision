#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller hook for pkg_resources and setuptools dependencies
修复 jaraco.text 和相关模块缺失问题
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 收集所有 jaraco 相关模块
hiddenimports = []

# jaraco 模块及其子模块
jaraco_modules = [
    'jaraco',
    'jaraco.text',
    'jaraco.functools',  
    'jaraco.context',
    'jaraco.collections',
    'jaraco.itertools',
    'jaraco.classes',
]

hiddenimports.extend(jaraco_modules)

# 尝试收集所有 jaraco 子模块
try:
    jaraco_submodules = collect_submodules('jaraco')
    hiddenimports.extend(jaraco_submodules)
except ImportError:
    pass

# setuptools 相关模块
setuptools_modules = [
    'setuptools',
    'setuptools._distutils',
    'setuptools.build_meta',
    'pkg_resources',
    'pkg_resources._vendor',
    'pkg_resources.extern',
]

hiddenimports.extend(setuptools_modules)

# importlib 相关模块
importlib_modules = [
    'importlib_metadata',
    'importlib_metadata._adapters',
    'zipp',
]

hiddenimports.extend(importlib_modules)

# 收集数据文件
datas = []
try:
    # 收集 pkg_resources 的数据文件
    pkg_resources_data = collect_data_files('pkg_resources')
    datas.extend(pkg_resources_data)
except ImportError:
    pass

try:
    # 收集 jaraco 的数据文件
    jaraco_data = collect_data_files('jaraco')
    datas.extend(jaraco_data)
except ImportError:
    pass