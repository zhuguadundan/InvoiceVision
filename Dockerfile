# 使用官方 Python 3.11 镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖（包含OpenCV和OCR所需的图形库）
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libfontconfig1 \
    libopencv-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（合并安装减小层数）
RUN pip install --no-cache-dir -r requirements.txt flask flask-socketio gunicorn eventlet

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

# 设置入口点 - 默认启动Web界面
CMD ["python", "web_app.py"]