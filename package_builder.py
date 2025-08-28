#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
InvoiceVision 自动打包脚本
基于Embedded Python架构的完整部署包生成工具
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import subprocess

class InvoiceVisionPackager:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.build_dir = self.project_root / "build_package"
        self.dist_dir = self.project_root / "dist_package"
        
        # 获取版本信息
        self.version = self.get_version()
        self.package_name = f"InvoiceVision_v{self.version}_{datetime.now().strftime('%Y%m%d')}"
        
        print(f"🚀 InvoiceVision 打包工具")
        print(f"📦 项目根目录: {self.project_root}")
        print(f"📋 版本信息: {self.version}")
        print(f"📁 打包名称: {self.package_name}")
        print("=" * 60)

    def get_version(self):
        """获取版本信息"""
        try:
            # 尝试从offline_config.json读取版本
            config_path = self.project_root / "offline_config.json"
            if config_path.exists():
                import json
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('version', '2.0-embedded')
        except:
            pass
        
        # 默认版本
        return "2.0-embedded"
    
    def clean_build(self):
        """清理构建目录"""
        print("\n🧹 清理构建目录...")
        
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print(f"   删除旧的构建目录: {self.build_dir}")
        
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print(f"   删除旧的分发目录: {self.dist_dir}")
        
        # 创建新目录
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        
        print("   ✅ 构建目录清理完成")

    def copy_core_files(self):
        """复制核心程序文件"""
        print("\n📄 复制核心程序文件...")
        
        # 核心Python文件
        core_files = [
            'InvoiceVision.py',
            'OCRInvoice.py', 
            'MainAction.py',
            'PDF2IMG.py',
            'ModelManager.py',
            'resource_utils.py',
            'main.py',
            'offline_config.json'
        ]
        
        copied_count = 0
        for file_name in core_files:
            src_file = self.project_root / file_name
            if src_file.exists():
                shutil.copy2(src_file, self.build_dir / file_name)
                print(f"   ✅ {file_name}")
                copied_count += 1
            else:
                print(f"   ⚠️ 文件不存在: {file_name}")
        
        print(f"   📊 复制核心文件: {copied_count}/{len(core_files)}")

    def copy_resources(self):
        """复制资源目录"""
        print("\n📁 复制资源目录...")
        
        # 需要复制的目录
        resource_dirs = [
            'static',
            'templates', 
            'models',
            'input',
            'output'
        ]
        
        copied_dirs = 0
        for dir_name in resource_dirs:
            src_dir = self.project_root / dir_name
            if src_dir.exists() and src_dir.is_dir():
                dst_dir = self.build_dir / dir_name
                shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns(
                    '*.pyc', '__pycache__', '*.pyo', '.git*', '.DS_Store'
                ))
                print(f"   ✅ {dir_name}/ ({self.get_dir_size(dst_dir)})")
                copied_dirs += 1
            else:
                # 创建空目录
                (self.build_dir / dir_name).mkdir(exist_ok=True)
                print(f"   📁 创建空目录: {dir_name}/")
        
        print(f"   📊 处理资源目录: {copied_dirs} 个现有目录")

    def copy_python_embedded(self):
        """复制embedded Python环境"""
        print("\n🐍 复制Python Embedded环境...")
        
        src_python = self.project_root / "python-embed"
        if not src_python.exists():
            print("   ❌ 错误: 未找到python-embed目录!")
            print("   💡 请确保已按照方案A设置了embedded Python环境")
            return False
        
        dst_python = self.build_dir / "python-embed"
        
        # 复制整个python-embed目录
        print(f"   📦 复制Python环境 ({self.get_dir_size(src_python)})...")
        shutil.copytree(src_python, dst_python, ignore=shutil.ignore_patterns(
            '__pycache__', '*.pyc', '*.pyo', '.git*'
        ))
        
        # 验证关键文件
        critical_files = ['python.exe', 'python311.dll', 'python311._pth']
        for file_name in critical_files:
            if (dst_python / file_name).exists():
                print(f"   ✅ {file_name}")
            else:
                print(f"   ❌ 缺少关键文件: {file_name}")
                return False
        
        # 检查site-packages
        site_packages = dst_python / "Lib" / "site-packages"
        if site_packages.exists():
            package_count = len(list(site_packages.iterdir()))
            print(f"   ✅ site-packages/ ({package_count} 个包)")
        else:
            print(f"   ⚠️ 未找到site-packages目录")
        
        print("   ✅ Python环境复制完成")
        return True

    def create_launcher(self):
        """创建启动脚本"""
        print("\n🚀 创建启动脚本...")
        
        # Windows批处理启动脚本
        bat_content = '''@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title InvoiceVision - 离线发票OCR识别系统

echo.
echo ╔══════════════════════════════════════╗
echo ║          InvoiceVision v{version}          ║
echo ║        离线发票OCR识别系统           ║
echo ╚══════════════════════════════════════╝
echo.
echo 正在启动程序，请稍候...
echo.

python-embed\\python.exe main.py

if errorlevel 1 (
    echo.
    echo ❌ 程序启动失败，请检查错误信息
    echo 💡 如需帮助，请查看 README_DEPLOYMENT.md
    echo.
    pause
) else (
    echo.
    echo ✅ 程序已正常退出
)'''.format(version=self.version)
        
        bat_file = self.build_dir / "InvoiceVision.bat"
        with open(bat_file, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        print(f"   ✅ InvoiceVision.bat")
        
        # PowerShell启动脚本（备用）
        ps1_content = '''# InvoiceVision PowerShell启动脚本
Set-Location -Path $PSScriptRoot
Write-Host "正在启动InvoiceVision..." -ForegroundColor Green
& ".\\python-embed\\python.exe" "main.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "启动失败，错误代码: $LASTEXITCODE" -ForegroundColor Red
    Read-Host "按任意键退出"
}'''
        
        ps1_file = self.build_dir / "InvoiceVision.ps1"
        with open(ps1_file, 'w', encoding='utf-8') as f:
            f.write(ps1_content)
        
        print(f"   ✅ InvoiceVision.ps1 (备用)")

    def create_documentation(self):
        """创建文档文件"""
        print("\n📚 创建部署文档...")
        
        # 复制现有的README_DEPLOYMENT.md
        src_readme = self.project_root / "README_DEPLOYMENT.md"
        if src_readme.exists():
            shutil.copy2(src_readme, self.build_dir / "README_DEPLOYMENT.md")
            print("   ✅ README_DEPLOYMENT.md")
        
        # 创建快速开始指南
        quick_start = '''# InvoiceVision 快速开始

## 🚀 立即使用

1. **解压文件包**到任意目录
2. **双击启动** `InvoiceVision.bat`
3. **开始使用**离线发票OCR识别功能

## 📋 系统要求

- Windows 7 x64 或更高版本
- 200MB 磁盘空间
- 2GB 内存

## 🔧 故障排除

**启动失败？**
- 确保解压到英文路径
- 确保没有杀毒软件阻止
- 以管理员身份运行

**OCR识别慢？**
- 首次运行会下载模型，请耐心等待
- 后续使用会变快

## 💡 技术支持

如遇问题，请查看 `README_DEPLOYMENT.md` 详细文档。

---
版本: {version} | 构建时间: {build_time}
'''.format(version=self.version, build_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        quick_file = self.build_dir / "快速开始.txt"
        with open(quick_file, 'w', encoding='utf-8') as f:
            f.write(quick_start)
        
        print("   ✅ 快速开始.txt")

    def create_package(self):
        """创建最终压缩包"""
        print("\n📦 创建部署压缩包...")
        
        # 创建ZIP压缩包
        zip_path = self.dist_dir / f"{self.package_name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for file_path in self.build_dir.rglob('*'):
                if file_path.is_file():
                    # 计算相对路径
                    arcname = file_path.relative_to(self.build_dir)
                    zipf.write(file_path, arcname)
        
        # 获取压缩包大小
        zip_size = self.get_file_size(zip_path)
        build_size = self.get_dir_size(self.build_dir)
        
        print(f"   ✅ 压缩包创建完成:")
        print(f"      📁 原始大小: {build_size}")
        print(f"      📦 压缩大小: {zip_size}")
        print(f"      💾 保存位置: {zip_path}")
        
        return zip_path

    def get_dir_size(self, path):
        """获取目录大小的友好显示"""
        total_size = sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file())
        return self.format_size(total_size)
    
    def get_file_size(self, file_path):
        """获取文件大小的友好显示"""
        size = Path(file_path).stat().st_size
        return self.format_size(size)
    
    def format_size(self, size_bytes):
        """格式化文件大小显示"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def cleanup_processes(self):
        """清理可能的残留进程"""
        print("\n[CLEANUP] 清理残留进程...")
        
        import psutil
        import os
        
        try:
            current_pid = os.getpid()
            cleaned_count = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # 跳过当前进程
                    if proc.info['pid'] == current_pid:
                        continue
                    
                    name = proc.info['name'].lower()
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    
                    # 查找可能的打包相关进程
                    if (('python' in name and 
                         ('package_builder' in cmdline or 
                          'InvoiceVision' in cmdline or
                          'build_package' in cmdline)) or
                        ('invoicevision' in name)):
                        
                        print(f"   发现可能的残留进程: PID {proc.info['pid']} - {proc.info['name']}")
                        
                        # 温和终止
                        try:
                            proc.terminate()
                            proc.wait(timeout=5)
                            print(f"   [OK] 已终止进程: {proc.info['pid']}")
                            cleaned_count += 1
                        except psutil.TimeoutExpired:
                            # 强制终止
                            proc.kill()
                            print(f"   [FORCE] 强制终止进程: {proc.info['pid']}")
                            cleaned_count += 1
                        except psutil.NoSuchProcess:
                            print(f"   [INFO] 进程已退出: {proc.info['pid']}")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    print(f"   [WARNING] 处理进程时出错: {e}")
            
            if cleaned_count == 0:
                print("   [OK] 未发现需要清理的进程")
            else:
                print(f"   [STATS] 清理了 {cleaned_count} 个进程")
                
        except ImportError:
            print("   [WARNING] 无法导入psutil，跳过进程清理")
        except Exception as e:
            print(f"   [ERROR] 进程清理失败: {e}")

    def run_package(self):
        """执行完整打包流程"""
        try:
            # 检查先决条件
            if not (self.project_root / "python-embed").exists():
                print("❌ 错误: 未找到python-embed目录")
                print("💡 请先按照方案A设置embedded Python环境")
                return False
            
            # 执行打包步骤
            self.clean_build()
            self.copy_core_files()
            self.copy_resources()
            
            if not self.copy_python_embedded():
                return False
            
            self.create_launcher()
            self.create_documentation()
            zip_path = self.create_package()
            
            # 打包完成
            print("\n" + "=" * 60)
            print("[SUCCESS] 打包完成!")
            print(f"[PACKAGE] 部署包: {zip_path}")
            print("[INFO] 使用说明:")
            print("   1. 将压缩包发送给用户")
            print("   2. 用户解压到任意目录")
            print("   3. 双击 InvoiceVision.bat 启动")
            print("=" * 60)
            
            # 清理可能的残留进程
            self.cleanup_processes()
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] 打包失败: {e}")
            import traceback
            traceback.print_exc()
            
            # 即使失败也要清理进程
            try:
                self.cleanup_processes()
            except:
                pass
                
            return False

def main():
    """主函数"""
    print("InvoiceVision 自动打包工具")
    print("基于Embedded Python架构\n")
    
    packager = InvoiceVisionPackager()
    
    # 确认打包
    response = input("是否开始打包? (y/N): ").lower().strip()
    if response not in ('y', 'yes', '是'):
        print("取消打包")
        return
    
    # 执行打包
    success = packager.run_package()
    
    if success:
        input("\n按任意键退出...")
    else:
        input("\n打包失败，按任意键退出...")

if __name__ == "__main__":
    main()