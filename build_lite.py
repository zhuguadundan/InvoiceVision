#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InvoiceVision 模型分离版打包脚本
创建小体积的exe文件，模型文件独立管理
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import platform
import time

def main():
    print("="*60)
    print("        InvoiceVision 模型分离版打包工具")
    print("="*60)
    
    # 显示系统信息
    print(f"系统: {platform.system()} {platform.version()}")
    print(f"Python: {platform.python_version()}")
    print(f"架构: {platform.machine()}")
    
    # 检查PyInstaller是否安装
    print("\n检查依赖...")
    try:
        import PyInstaller
        print(f"[OK] PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print("[ERROR] PyInstaller未安装，请运行: pip install pyinstaller")
        input("按回车键退出...")
        return
    
    # 检查必要文件
    required_files = [
        'InvoiceVision.py',
        'OCRInvoice.py', 
        'MainAction.py',
        'PDF2IMG.py',
        'resource_utils.py',
        'ModelManager.py',
        'offline_config.json',
        'InvoiceVision.spec'
    ]
    
    print("\n检查必要文件...")
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"[OK] {file}")
        else:
            print(f"[MISSING] {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n[ERROR] 缺少必要文件: {missing_files}")
        input("按回车键退出...")
        return
    
    print("\n[OK] 所有必要文件已就绪")
    
    # 检查hooks目录
    hooks_dir = Path("pyinstaller_hooks")
    if hooks_dir.exists() and hooks_dir.is_dir():
        print(f"[OK] Hooks目录存在，包含 {len(list(hooks_dir.glob('*.py')))} 个hook文件")
    else:
        print("[WARNING] Hooks目录不存在或为空")
    
    # 清理旧文件
    print("\n清理旧文件...")
    cleanup_dirs = ['build', 'dist', '__pycache__']
    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            try:
                if dir_name == '__pycache__':
                    for root, dirs, files in os.walk(dir_name, topdown=False):
                        for file in files:
                            os.remove(os.path.join(root, file))
                        for dir in dirs:
                            os.rmdir(os.path.join(root, dir))
                    os.rmdir(dir_name)
                else:
                    shutil.rmtree(dir_name)
                print(f"[CLEANED] {dir_name}")
            except PermissionError as e:
                if dir_name == 'dist':
                    print(f"[ERROR] 清理 {dir_name} 失败: {e}")
                    print("[INFO] 可能有InvoiceVision.exe正在运行")
                    print("[INFO] 请手动关闭所有InvoiceVision进程后重试")
                    input("按回车键退出...")
                    return
                else:
                    print(f"[WARNING] 清理 {dir_name} 失败: {e}")
            except Exception as e:
                print(f"[WARNING] 清理 {dir_name} 失败: {e}")
    
    # 开始打包
    print("\n开始打包（模型分离版）...")
    print("优势：")
    print("  - exe文件小（约50-100MB vs 300MB+）")
    print("  - 首次启动自动下载模型")
    print("  - 便于模型更新和管理")
    print("  - 支持完全离线部署")
    
    start_time = time.time()
    
    try:
        # 设置环境变量，减少编译警告
        env = os.environ.copy()
        env['PADDLE_SKIP_SIGNALS_CHECK'] = '1'  # 跳过信号检查
        env['PADDLE_SILENT_MODE'] = '1'         # 静默模式
        env['PADDLE_DISABLE_WARNINGS'] = '1'    # 禁用警告
        
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', 'InvoiceVision.spec']
        print(f"\n执行命令: {' '.join(cmd)}")
        print("-" * 50)
        
        # 实时显示输出
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                text=True, universal_newlines=True, env=env)
        
        for line in process.stdout:
            print(line, end='')
            sys.stdout.flush()
        
        process.wait()
        print("-" * 50)
        
        end_time = time.time()
        build_time = end_time - start_time
        
        if process.returncode == 0:
            exe_path = Path("dist/InvoiceVision.exe")
            if exe_path.exists():
                file_size = exe_path.stat().st_size / 1024 / 1024
                print("\n[SUCCESS] 打包成功！")
                print(f"文件位置: {exe_path.absolute()}")
                print(f"文件大小: {file_size:.1f} MB")
                print(f"构建时间: {build_time:.1f} 秒")
                
                # 创建使用说明和部署脚本
                create_readme()
                create_deployment_script()
                copy_additional_files()
                
                print("\n📦 部署方式：")
                print("1. 单文件模式：只需InvoiceVision.exe")
                print("   - 首次启动自动提示下载模型")
                print("   - 模型下载到exe同目录的models文件夹")
                
                print("\n2. 离线包模式：")
                print("   - 手动下载模型文件")
                print("   - 与exe放在同一目录")
                print("   - 完全离线使用")
                
                print("\n3. 部署包模式：")
                print("   - 运行 dist/deploy.bat 自动部署")
                print("   - 包含所有必要文件和说明")
                
            else:
                print("[ERROR] 打包失败：未找到生成的exe文件")
        else:
            print(f"\n[ERROR] 打包失败，退出码: {process.returncode}")
            print("请检查上面的错误信息")
            
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断打包过程")
    except Exception as e:
        print(f"\n[ERROR] 打包过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n打包脚本执行完成。")

def create_readme():
    """创建使用说明"""
    readme_content = """# InvoiceVision 模型分离版使用说明

## 快速开始

### 方式一：自动下载模式（推荐）
1. 双击 `InvoiceVision.exe` 启动
2. 首次运行会提示下载模型文件（约100MB）
3. 选择"是"进行自动下载
4. 下载完成后即可正常使用

### 方式二：手动安装模式
1. 下载模型文件包：
   - PP-OCRv5_server_det: https://paddleocr.bj.bcebos.com/PP-OCRv4/server/inference/PP-OCRv4_server_det_infer.tar
   - PP-OCRv5_server_rec: https://paddleocr.bj.bcebos.com/PP-OCRv4/server/inference/PP-OCRv4_server_rec_infer.tar
   - PP-LCNet_x1_0_textline_ori: https://paddleocr.bj.bcebos.com/dygraph_v2.1/PP-OCRv3/dygraph/cls_infer.tar

2. 创建目录结构：
   ```
   InvoiceVision.exe所在目录/
   ├── InvoiceVision.exe
   └── models/
       ├── PP-OCRv5_server_det/
       ├── PP-OCRv5_server_rec/
       └── PP-LCNet_x1_0_textline_ori/
   ```

3. 解压模型文件到对应目录
4. 启动程序即可使用

## 优势

✅ **小体积**：exe文件约50-100MB（vs传统版300MB+）
✅ **灵活部署**：支持在线下载和离线安装
✅ **便于更新**：模型文件可以独立更新
✅ **完全离线**：下载完成后无需网络连接

## 系统要求

- Windows 7/8/10/11 (64位)
- 内存：4GB+ 推荐
- 磁盘空间：200MB（含模型）
- 网络：首次运行下载模型时需要

## 注意事项

- 首次启动模型加载可能较慢
- 支持中文增值税发票OCR识别
- 支持PDF和图片文件批量处理
- 生成Excel格式识别结果

## 故障排除

**问题1：提示"模型文件缺失"**
- 解决：选择自动下载或按手动安装步骤操作

**问题2：下载失败**
- 解决：检查网络连接，或使用手动安装模式

**问题3：程序无法启动**
- 解决：确保系统是64位Windows，安装Visual C++ Redistributable

## 技术支持

如有问题请检查：
1. 系统兼容性
2. 模型文件完整性
3. 网络连接状况

---
InvoiceVision 模型分离版 - 更小、更灵活的发票OCR解决方案
"""
    
    with open("dist/README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("[SUCCESS] 使用说明已创建：dist/README.md")

def create_deployment_script():
    """创建部署脚本"""
    bat_content = """@echo off
chcp 65001 >nul
echo ============================================
echo        InvoiceVision 自动部署脚本
echo ============================================
echo.

REM 检查是否存在InvoiceVision.exe
if not exist "InvoiceVision.exe" (
    echo [ERROR] 未找到 InvoiceVision.exe
    echo 请确保此脚本与 InvoiceVision.exe 在同一目录
    pause
    exit /b 1
)

echo [OK] 找到 InvoiceVision.exe

REM 创建必要的目录结构
if not exist "models" (
    echo [INFO] 创建 models 目录...
    mkdir models
)

if not exist "output" (
    echo [INFO] 创建 output 目录...
    mkdir output
)

REM 检查模型文件
echo.
echo [INFO] 检查模型文件...
set models_found=0
if exist "models\\PP-OCRv5_server_det" set /a models_found+=1
if exist "models\\PP-OCRv5_server_rec" set /a models_found+=1
if exist "models\\PP-LCNet_x1_0_textline_ori" set /a models_found+=1

if %models_found% equ 3 (
    echo [OK] 所有模型文件已就绪
) else if %models_found% gtr 0 (
    echo [WARNING] 发现 %models_found%/3 个模型文件
    echo 请手动下载缺失的模型文件
) else (
    echo [INFO] 未找到模型文件
    echo 首次运行时程序将自动下载
)

echo.
echo ============================================
echo        部署完成！
echo ============================================
echo.
echo 现在您可以：
echo 1. 双击 InvoiceVision.exe 启动程序
echo 2. 查看 README.md 了解详细使用说明
echo 3. 将发票文件拖拽到程序中进行识别
echo.
echo 按任意键启动程序...
pause >nul

start InvoiceVision.exe
"""
    
    with open("dist/deploy.bat", 'w', encoding='gbk') as f:
        f.write(bat_content)
    
    print("[SUCCESS] 部署脚本已创建：dist/deploy.bat")

def copy_additional_files():
    """复制额外的文件到dist目录"""
    additional_files = [
        'README.md',
        '使用说明.md',
        'LICENSE',
        'requirements.txt',
        'offline_config.json'
    ]
    
    for file_name in additional_files:
        if os.path.exists(file_name):
            try:
                shutil.copy2(file_name, "dist/")
                print(f"[COPIED] {file_name} -> dist/")
            except Exception as e:
                print(f"[ERROR] 复制 {file_name} 失败: {e}")

if __name__ == "__main__":
    main()