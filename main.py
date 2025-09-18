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

# 以模块方式启动，避免使用 exec
if __name__ == "__main__":
    try:
        from InvoiceVision import main as run_app
        run_app()
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        # 仅在交互式终端中暂停，避免无头环境卡住
        try:
            if sys.stdin and sys.stdin.isatty():
                input("按任意键退出...")
        except Exception:
            pass
        sys.exit(1)

