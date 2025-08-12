#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InvoiceVision 打包前检查脚本
验证所有依赖和配置是否正确
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"[ERROR] Python版本过低，需要3.8+，当前：{version.major}.{version.minor}.{version.micro}")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n检查依赖包...")
    required_packages = {
        'PyQt5': 'PyQt5',
        'paddleocr': 'paddleocr',
        'paddlepaddle': 'paddle',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'PIL': 'PIL',
        'fitz': 'fitz',
        'PyInstaller': 'PyInstaller',
        'pandas': 'pandas',
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            spec = importlib.util.find_spec(import_name)
            if spec is not None:
                # 尝试获取版本信息
                try:
                    module = importlib.import_module(import_name)
                    version = getattr(module, '__version__', '未知版本')
                    print(f"[OK] {package_name}: {version}")
                except:
                    print(f"[OK] {package_name}")
            else:
                print(f"[MISSING] {package_name}")
                missing_packages.append(package_name)
        except Exception as e:
            print(f"[ERROR] {package_name}: {e}")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n[ERROR] 缺少依赖包: {missing_packages}")
        print("请运行以下命令安装：")
        print("pip install -r requirements.txt")
        return False
    
    print("[OK] 所有依赖包已安装")
    return True

def check_source_files():
    """检查源代码文件"""
    print("\n检查源代码文件...")
    required_files = [
        'InvoiceVision.py',
        'OCRInvoice.py',
        'MainAction.py', 
        'PDF2IMG.py',
        'ModelManager.py',
        'resource_utils.py',
        'offline_config.json',
        'InvoiceVision.spec'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        if os.path.exists(file_name):
            file_size = os.path.getsize(file_name)
            print(f"[OK] {file_name} ({file_size} bytes)")
        else:
            print(f"[MISSING] {file_name}")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n[ERROR] 缺少源文件: {missing_files}")
        return False
    
    print("[OK] 所有源文件存在")
    return True

def check_hooks():
    """检查hooks文件"""
    print("\n检查hooks文件...")
    hooks_dir = Path("pyinstaller_hooks")
    
    if not hooks_dir.exists():
        print("[WARNING] hooks目录不存在")
        return True  # 不是致命错误
    
    hook_files = list(hooks_dir.glob("*.py"))
    if not hook_files:
        print("[WARNING] hooks目录为空")
        return True
    
    print(f"[OK] 找到 {len(hook_files)} 个hook文件:")
    for hook_file in hook_files:
        print(f"  - {hook_file.name}")
    
    return True

def check_configuration():
    """检查配置文件"""
    print("\n检查配置文件...")
    
    # 检查offline_config.json
    config_file = "offline_config.json"
    if os.path.exists(config_file):
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"[OK] {config_file} 配置正确")
            print(f"  - offline_mode: {config.get('offline_mode', 'N/A')}")
            print(f"  - models_path: {config.get('models_path', 'N/A')}")
            print(f"  - use_gpu: {config.get('use_gpu', 'N/A')}")
            print(f"  - lang: {config.get('lang', 'N/A')}")
        except Exception as e:
            print(f"[ERROR] {config_file} 格式错误: {e}")
            return False
    else:
        print(f"[MISSING] {config_file}")
        return False
    
    return True

def check_disk_space():
    """检查磁盘空间"""
    print("\n检查磁盘空间...")
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free // (1024**3)
        
        if free_gb < 5:
            print(f"[WARNING] 磁盘空间不足：{free_gb}GB（建议至少5GB）")
        elif free_gb < 2:
            print(f"[ERROR] 磁盘空间严重不足：{free_gb}GB（需要至少2GB）")
            return False
        else:
            print(f"[OK] 可用磁盘空间：{free_gb}GB")
        
        return True
    except Exception as e:
        print(f"[ERROR] 检查磁盘空间失败: {e}")
        return False

def run_test_import():
    """运行测试导入"""
    print("\n测试关键模块导入...")
    test_modules = [
        'PyQt5.QtWidgets',
        'paddleocr',
        'pandas',
        'fitz',
        'OCRInvoice',
        'ModelManager',
        'MainAction',
        'PDF2IMG'
    ]
    
    failed_imports = []
    
    for module_name in test_modules:
        try:
            __import__(module_name)
            print(f"[OK] {module_name}")
        except Exception as e:
            print(f"[ERROR] {module_name}: {e}")
            failed_imports.append(module_name)
    
    if failed_imports:
        print(f"\n[ERROR] {len(failed_imports)} 个模块导入失败")
        return False
    
    print("[OK] 所有模块导入成功")
    return True

def main():
    print("="*60)
    print("        InvoiceVision 打包前检查工具")
    print("="*60)
    
    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("源代码文件", check_source_files),
        ("Hooks文件", check_hooks),
        ("配置文件", check_configuration),
        ("磁盘空间", check_disk_space),
        ("模块导入", run_test_import),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        if check_func():
            passed += 1
        else:
            print(f"[FAIL] {check_name} 检查失败")
    
    print(f"\n{'='*60}")
    print(f"检查结果：{passed}/{total} 项通过")
    print(f"{'='*60}")
    
    if passed == total:
        print("[SUCCESS] 所有检查通过，可以开始打包！")
        print("\n运行打包命令：")
        print("python build_lite.py")
        return True
    else:
        print("[ERROR] 部分检查失败，请修复问题后再打包")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)