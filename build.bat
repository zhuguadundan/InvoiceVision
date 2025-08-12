@echo off
chcp 65001 >nul
echo ============================================
echo        InvoiceVision 一键打包脚本
echo ============================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

echo [OK] Python已就绪

REM 运行打包前检查
echo.
echo [STEP 1] 运行打包前检查...
python check_build.py
if %errorlevel% neq 0 (
    echo [ERROR] 打包前检查失败，请修复问题后重试
    pause
    exit /b 1
)

echo [OK] 打包前检查通过

REM 开始打包
echo.
echo [STEP 2] 开始打包...
python build_lite.py

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] 打包完成！
    echo.
    echo 生成的文件位置：
    echo   - 主程序：dist\InvoiceVision.exe
    echo   - 使用说明：dist\README.md
    echo   - 部署脚本：dist\deploy.bat
    echo.
    echo 部署方式：
    echo   1. 直接运行 dist\InvoiceVision.exe
    echo   2. 运行 dist\deploy.bat 自动部署
    echo.
) else (
    echo [ERROR] 打包失败，请查看上面的错误信息
)

pause