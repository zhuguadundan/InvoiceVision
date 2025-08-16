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
    
    # 分组检查，避免PaddleOCR中断其他检查
    basic_modules = [
        'PyQt5.QtWidgets',
        'pandas',
        'fitz'
    ]
    
    paddle_modules = [
        'paddleocr'
    ]
    
    custom_modules = [
        'OCRInvoice',
        'ModelManager', 
        'MainAction',
        'PDF2IMG'
    ]
    
    failed_imports = []
    
    # 检查基础模块
    print("检查基础模块...")
    for module_name in basic_modules:
        try:
            __import__(module_name)
            print(f"[OK] {module_name}")
        except Exception as e:
            print(f"[ERROR] {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
    
    # 检查PaddleOCR模块
    print("检查OCR模块...")
    for module_name in paddle_modules:
        try:
            __import__(module_name)
            print(f"[OK] {module_name}")
        except Exception as e:
            print(f"[ERROR] {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
    
    # 检查自定义模块
    print("检查自定义模块...")
    for module_name in custom_modules:
        try:
            __import__(module_name)
            print(f"[OK] {module_name}")
        except Exception as e:
            print(f"[ERROR] {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
    
    # 额外检查PaddleOCR相关子模块
    print("检查PaddleOCR子模块...")
    paddle_submodules = [
        'paddlex',
        'paddlex.modules', 
        'paddlex.modules.doc_vlm',
        'paddlex.modules.formula_recognition',
        'paddlex.utils.misc'
    ]
    
    for module_name in paddle_submodules:
        try:
            # 只有paddleocr成功导入才检查子模块
            paddleocr_ok = all('paddleocr' not in f[0] for f in failed_imports)
            if paddleocr_ok:
                # 先检查父模块
                parent_module = module_name.split('.')[0]
                try:
                    __import__(parent_module)
                    __import__(module_name)
                    print(f"[OK] {module_name}")
                except ImportError as e:
                    print(f"[ERROR] {module_name}: {e}")
                    failed_imports.append((module_name, str(e)))
            else:
                print(f"[SKIP] {module_name}: PaddleOCR 主模块缺失")
        except Exception as e:
            print(f"[ERROR] {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
    
    if failed_imports:
        print(f"\n=== 系统导入错误汇总 ===")
        print(f"共发现 {len(failed_imports)} 个模块导入失败:")
        
        # 分类显示错误
        framework_errors = [e for e in failed_imports if e[0] in ['PyQt5.QtWidgets']]
        paddle_errors = [e for e in failed_imports if e[0] in ['paddleocr']]
        data_errors = [e for e in failed_imports if e[0] in ['pandas']]
        pdf_errors = [e for e in failed_imports if e[0] in ['fitz']]
        custom_errors = [e for e in failed_imports if e[0] in ['OCRInvoice', 'ModelManager', 'MainAction', 'PDF2IMG']]
        
        if framework_errors:
            print("GUI框架错误:")
            for module, error in framework_errors:
                print(f"  - {module}: {error}")
        
        if paddle_errors:
            print("OCR引擎错误:")
            for module, error in paddle_errors:
                print(f"  - {module}: {error}")
        
        if data_errors:
            print("数据处理错误:")
            for module, error in data_errors:
                print(f"  - {module}: {error}")
        
        if pdf_errors:
            print("PDF处理错误:")
            for module, error in pdf_errors:
                print(f"  - {module}: {error}")
        
        if custom_errors:
            print("自定义模块错误:")
            for module, error in custom_errors:
                print(f"  - {module}: {error}")
        
        # 提供解决方案建议
        print("\n解决方案建议:")
        if framework_errors:
            print("GUI框架安装命令:")
            print("pip install PyQt5")
        
        if paddle_errors:
            print("PaddleOCR安装命令:")
            print("pip install paddleocr paddlepaddle")
            print("如果已打包到exe，请将缺失模块添加到 .spec 文件的 hiddenimports 中")
        
        if data_errors:
            print("数据处理安装命令:")
            print("pip install pandas")
        
        if pdf_errors:
            print("PDF处理安装命令:")
            print("pip install pymupdf")
        
        if custom_errors:
            print("自定义模块错误:")
            print("请确保项目结构完整，所有自定义模块文件存在")
        
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