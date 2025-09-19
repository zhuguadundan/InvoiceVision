#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行环境与模型自检脚本（离线优先）

用法：
  python diagnose.py            # 基础检查（依赖/模型）
  python diagnose.py --ocr      # 额外：尝试初始化 OCR 引擎
"""

import sys
import json
import platform
from pathlib import Path


def check_imports():
    status = {}
    mods = [
        ("PyQt5", "from PyQt5 import QtCore"),
        ("paddleocr", "import paddleocr"),
        ("paddlepaddle", "import paddle"),
        ("pymupdf", "import fitz"),
        ("pandas", "import pandas as pd"),
        ("opencv-python", "import cv2"),
        ("numpy", "import numpy as np"),
    ]
    for name, stmt in mods:
        try:
            exec(stmt, {})
            status[name] = True
        except Exception as e:
            status[name] = f"ERROR: {e}"
    return status


def check_models():
    try:
        from ModelManager import ModelManager
    except Exception:
        # 兜底：直接检查默认 models 结构
        root = Path("models")
        need = [
            root / "PP-OCRv5_mobile_det",
            root / "PP-OCRv5_mobile_rec",
            root / "ch_ppocr_mobile_v2.0_cls",
        ]
        info = {
            "models_dir": str(root.resolve()),
            "exists": root.exists(),
            "complete": all(p.exists() and any(p.iterdir()) for p in need),
            "models": {p.name: {"path": str(p), "exists": p.exists()} for p in need},
        }
        return info

    m = ModelManager()
    return m.get_models_info()


def try_initialize_ocr(mode: str = "快速"):
    try:
        from OCRInvoice import OfflineOCRInvoice
        ok = OfflineOCRInvoice.global_initialize_ocr(mode)
        return bool(ok)
    except Exception as e:
        return f"ERROR: {e}"


def main():
    want_ocr = "--ocr" in sys.argv

    print("=== InvoiceVision 自检 ===")
    print(f"Python: {platform.python_version()} | {platform.platform()}")

    print("\n[1/3] 依赖检查…")
    deps = check_imports()
    for k, v in deps.items():
        print(f" - {k}: {'OK' if v is True else v}")

    print("\n[2/3] 模型检查…")
    info = check_models()
    print(json.dumps(info, ensure_ascii=False, indent=2))

    if want_ocr:
        print("\n[3/3] OCR 引擎初始化（快速模式）…")
        res = try_initialize_ocr("快速")
        print(f" - OCR 初始化: {'OK' if res is True else res}")
    else:
        print("\n跳过 OCR 初始化（添加 --ocr 以尝试）")

    print("\n完成。")


if __name__ == "__main__":
    main()

