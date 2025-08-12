# PyInstaller hook for paddlex - 最小化版本
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

# 只包含核心模块，排除可选组件
hiddenimports = [
    'paddlex.utils.misc',
]

# 排除大型可选组件
excludedimports = [
    'paddlex.modules',
    'paddlex.inference',  
    'paddlex.repo_apis',
    'paddlex.datasets',
    'paddlex.pipelines',
    'paddlex.ops',
]

# 不收集数据文件，减少大小
datas = []