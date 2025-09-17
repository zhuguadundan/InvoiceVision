# 使用官方 Python 3.10 镜像作为基础镜像（Paddle生态兼容更好）
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装精简系统依赖（适配 headless OpenCV）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（在 requirements.txt 中统一声明）
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用程序文件
COPY . .

# 创建模型目录
RUN mkdir -p models

# 创建输入输出目录
RUN mkdir -p /app/input /app/output

# 设置权限
RUN chmod +x *.py

# 暴露端口（Web服务）
EXPOSE 8080

# 运行参数：生产环境使用 Gunicorn + Eventlet（与 Flask-SocketIO 兼容）
ENV SOCKETIO_ASYNC_MODE=eventlet

# 设置入口点 - 生产模式使用 Gunicorn
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:8080", "web_app:app"]