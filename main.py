#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
InvoiceVision 启动脚本 - Embedded Python版本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# 设置工作目录
os.chdir(str(project_root))

# 直接执行原始的InvoiceVision.py
if __name__ == "__main__":
    try:
        exec(open('InvoiceVision.py', encoding='utf-8').read())
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按任意键退出...")
        sys.exit(1)