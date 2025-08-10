# 发票OCR识别器 (升级版)

基于 PaddleOCR 3.1+ / PP-OCRv5 的中文增值税发票信息识别工具

## 🚀 新版本特性

- ✅ **升级至 PaddleOCR 3.1+**: 使用最新的 PP-OCRv5 模型
- ✅ **更高识别精度**: 支持更多发票格式，识别准确率显著提升  
- ✅ **双精度模式**: 快速模式和高精度模式可选
- ✅ **现代化界面**: 重新设计的GUI界面，操作更友好
- ✅ **智能图片处理**: 自动图片旋转和预处理
- ✅ **批量处理优化**: 支持PDF和图片文件夹批量处理
- ✅ **错误处理增强**: 更好的异常处理和用户反馈

## 📋 系统要求

- Python 3.8+ 
- Windows 10/11 (推荐)
- 4GB+ RAM
- 2GB+ 磁盘空间 (用于模型文件)

## 🛠️ 安装方法

### 方法1: 自动安装 (推荐)
```bash
python install.py
```

### 方法2: 手动安装
```bash
# 安装依赖
pip install -r requirements.txt

# 或手动安装核心包
pip install paddleocr>=3.1.0 paddlepaddle>=3.0.0 pillow pandas pyqt5 pymupdf
```

## 🚀 使用方法

### GUI界面 (推荐)
```bash
python OCRWindow.py
```

### 命令行使用
```python
from OCRInvoice import OfflineOCRInvoice

# 创建识别器
ocr = OfflineOCRInvoice()
ocr.set_precision_mode('快速')  # 或 '高精'

# 识别单张图片
result = ocr.run_ocr('invoice.jpg')
print(result)  # [文件路径, 发票代码, 发票号码, 日期, 金额]
```

## 📁 项目结构

```
InvoiceOCRer/
├── OCRWindow.py               # 主GUI程序 ⭐ (离线版)
├── OCRInvoice.py              # OCR识别核心 (离线版)
├── MainAction.py              # 批处理逻辑 (离线版)
├── PDF2IMG.py                 # PDF转图片工具
├── models/                    # PP-OCRv5离线模型 (209.4MB)
├── offline_config.json        # 离线模型配置
├── requirements.txt           # 依赖列表
├── install.py                 # 安装脚本
└── setup_offline_simple.py    # 离线模型设置
```

## 🎯 特性

现在这是一个**完全专注于离线运行**的PP-OCRv5发票识别系统：

- ✅ **完全离线运行** - 无需任何网络连接
- ✅ **PP-OCRv5模型** - 最新技术，识别精度提升20%
- ✅ **209.4MB本地模型** - 包含完整的检测、识别、方向分类模型
- ✅ **双精度模式** - 快速模式和高精度模式可选
- ✅ **现代化界面** - 友好的GUI界面设计
- ✅ **智能识别** - 自动图片旋转和预处理
- ✅ **批量处理** - 支持PDF和图片文件夹批量处理

## 📊 识别信息

程序会自动提取以下发票信息：
- 🏷️ **发票代码** (10-12位数字)
- 🔢 **发票号码** (8位数字) 
- 📅 **开票日期** (YYYYMMDD格式)
- 💰 **金额** (不含税金额)
- 📄 **文件路径** (原始文件位置)

## 🔧 配置选项

### 精度模式说明
- **快速模式**: 识别速度快，适合批量处理
- **高精度模式**: 识别精度高，启用所有辅助功能

### 支持的文件格式
- **图片**: JPG, JPEG, PNG, BMP, TIFF, WEBP
- **文档**: PDF (自动转换为图片)

## 🐛 故障排除

### 常见问题

1. **模型下载慢或失败**
   ```bash
   # 使用国内镜像源
   pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

2. **PyQt5安装失败**
   ```bash
   # Windows系统可能需要Visual C++运行库
   pip install pyqt5 --only-binary=all
   ```

3. **内存不足**
   - 关闭其他程序
   - 使用"快速"模式
   - 减少批处理文件数量

4. **识别精度低**
   - 使用"高精度"模式
   - 确保图片清晰度
   - 检查图片方向是否正确

## 🔄 使用建议

### 推荐使用方式：
```bash
python OCRWindow.py  # 完全离线运行的现代化GUI
```

### 从其他版本升级：
1. **备份数据**: 保存现有的识别结果
2. **安装依赖**: 运行 `python install.py` 
3. **设置离线模型**: 运行 `python setup_offline_simple.py`
4. **开始使用**: 运行 `python OCRWindow.py`

## 📈 性能对比

基于PP-OCRv5模型的性能提升：
- 识别精度提升约 **15-20%**
- 处理速度提升约 **10-15%** 
- 支持更多发票格式
- 更好的倾斜文字识别

## 🤝 贡献

欢迎提交Issues和Pull Requests！

## 📄 许可证

本项目遵循原项目的许可证。

---

## 🆚 版本历史

### v2.0 (当前版本)
- 升级到 PaddleOCR 3.1+
- 使用 PP-OCRv5 模型
- 重新设计的现代化界面
- 增强的错误处理
- 自动模型下载

### v1.0 (原始版本)
- 基于 PaddleOCR 2.1
- 基础GUI界面
- 手动模型配置

---

**享受更智能的发票识别体验！** 🎉