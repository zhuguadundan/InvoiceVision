# InvoiceVision - 智能发票OCR识别器

基于 PaddleOCR 的离线中文发票OCR识别系统，支持批量处理和多种格式。

## 快速开始

### Docker运行（推荐）

镜像地址：[zhugua/invoicevision](https://hub.docker.com/repository/docker/zhugua/invoicevision/general)

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 源码运行
```bash
python install.py        # 安装依赖
python InvoiceVision.py   # 启动程序
```

## 系统要求

- **Docker**: 内存 4GB+
- **源码**: Python 3.8+，内存 4GB+

## 使用方法

1. 选择精度模式（快速/高精）
2. 选择文件或文件夹
3. 开始处理并导出Excel

## 故障排除

- **Docker无法启动**: 检查 `docker --version`
- **模型下载失败**: 运行 `python setup_offline_simple.py`
- **识别精度低**: 切换到"高精度"模式

## 许可证

MIT 许可证

## 致谢

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR引擎
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架