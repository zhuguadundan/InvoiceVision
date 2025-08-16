@echo off
echo 启动 InvoiceVision Web服务...

REM 检查镜像是否存在
docker image inspect invoice-vision:latest > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 镜像不存在，请先运行 build-docker.bat 构建镜像
    pause
    exit /b 1
)

REM 创建必要的目录
if not exist input mkdir input
if not exist output mkdir output

REM 启动服务
echo 启动Web服务中...
docker-compose up

echo.
echo Web界面访问地址: http://localhost:8080
echo.

pause