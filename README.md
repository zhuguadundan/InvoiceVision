# InvoiceVision - 桌面版（GUI）

基于 PaddleOCR 的离线中文发票OCR识别器，提供 Windows 桌面图形界面，支持批量处理与 Excel 导出。

## 快速开始（GUI）

1) 解压部署包，双击 `InvoiceVision.bat` 启动；或源码方式：

```bash
python install.py        # 安装依赖（首次）
python InvoiceVision.py  # 启动GUI
```

2) 首次启动如缺少模型，按界面提示“下载轻量模型”或将模型文件夹复制到 `models/`。

## 系统要求

- Windows 7 x64 或更高版本
- 内存 2GB+（建议 4GB）

## 使用步骤

- 选择要处理的 PDF 或图片文件夹
- 开始处理，识别结果在界面汇总，可导出为 Excel

## 故障排除

- 启动失败：确认解压路径无中文空格；以管理员身份运行
- 模型缺失：在弹窗中点击“下载轻量模型”，或手动复制到 `models/`
- 识别慢：老旧电脑可保持默认“轻量模型”，避免使用大型模型

## 许可证

MIT 许可证

## 致谢

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR 引擎
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
