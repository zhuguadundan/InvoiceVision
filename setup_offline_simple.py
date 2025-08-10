#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线模型设置脚本 (简化版)
"""

import os
import shutil
import json
from pathlib import Path

def setup_offline_models():
    """设置离线模型"""
    print("=" * 60)
    print("离线模型设置")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    local_models_dir = base_dir / "models"
    local_models_dir.mkdir(exist_ok=True)
    
    # PaddleX模型路径
    username = os.getenv('USERNAME', 'user')
    paddlex_path = Path(f"C:/Users/{username}/.paddlex/official_models")
    
    print(f"检查PaddleX模型路径: {paddlex_path}")
    
    if not paddlex_path.exists():
        print("未找到PaddleX模型目录")
        print("请先运行PaddleOCR程序让它自动下载模型")
        return False
    
    # 查找并复制模型
    copied_count = 0
    config = {
        "offline_mode": True,
        "models": {},
        "use_gpu": False,
        "lang": "ch"
    }
    
    for model_dir in paddlex_path.iterdir():
        if model_dir.is_dir():
            model_name = model_dir.name
            local_model_path = local_models_dir / model_name
            
            print(f"处理模型: {model_name}")
            
            if not local_model_path.exists():
                try:
                    print(f"  复制到: {local_model_path}")
                    shutil.copytree(model_dir, local_model_path)
                    copied_count += 1
                except Exception as e:
                    print(f"  复制失败: {e}")
                    continue
            else:
                print(f"  已存在，跳过")
            
            # 配置模型路径
            if "det" in model_name.lower():
                config["models"]["det_model_dir"] = str(local_model_path)
            elif "rec" in model_name.lower():
                config["models"]["rec_model_dir"] = str(local_model_path)
            elif "textline" in model_name.lower() or "cls" in model_name.lower():
                config["models"]["cls_model_dir"] = str(local_model_path)
    
    # 保存配置文件
    config_file = base_dir / "offline_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n复制了 {copied_count} 个新模型")
    print(f"配置文件已保存: {config_file}")
    
    # 显示模型状态
    print("\n本地模型:")
    total_size = 0
    for model_dir in local_models_dir.iterdir():
        if model_dir.is_dir():
            print(f"  {model_dir.name}/")
            dir_size = 0
            for file_path in model_dir.rglob("*"):
                if file_path.is_file():
                    file_size = file_path.stat().st_size / (1024 * 1024)
                    dir_size += file_size
            total_size += dir_size
            print(f"    大小: {dir_size:.1f} MB")
    
    print(f"\n总模型大小: {total_size:.1f} MB")
    print("离线模型设置完成!")
    
    return True

if __name__ == "__main__":
    setup_offline_models()