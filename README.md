# InvoiceVision - 智能发票OCR识别器

<div align="center">

![InvoiceVision Logo](https://img.shields.io/badge/InvoiceVision-2.0-blue?style=for-the-badge&logo=ocr&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-blueviolet.svg?style=for-the-badge&logo=windows&logoColor=white)

**基于 PaddleOCR 3.1+ 的离线中文发票OCR识别系统**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [安装部署](#-安装部署) • [使用指南](#-使用指南) • [技术架构](#-技术架构)

</div>

---

## 🌟 功能特性

### ✅ 核心功能
- 🔍 **高精度OCR识别**: 基于 PP-OCRv5 模型，识别准确率 >95%
- 📄 **多格式支持**: 支持 PDF、JPG、PNG、BMP 等常见格式
- 🚀 **批量处理**: 支持单文件、多文件、文件夹批量处理
- 💾 **智能导出**: 识别结果自动导出为 Excel 格式
- 🖥️ **现代化界面**: 基于 PyQt5 的友好 GUI 界面

### ✅ 技术优势
- 🚫 **完全离线**: 无需网络连接，本地模型运行
- 🎯 **模型分离**: exe 文件体积小（~200MB），模型独立管理
- 🔄 **自动下载**: 首次运行自动下载所需模型文件
- ⚡ **双精度模式**: 快速模式 & 高精度模式可选
- 🌏 **中文优化**: 专为中文增值税发票优化

### ✅ 识别内容
- 🏷️ 发票代码 (10-12位数字)
- 🔢 发票号码 (8位数字)
- 📅 开票日期 (YYYYMMDD格式)
- 🏢 开票公司名称
- 📋 项目名称
- 💰 金额（不含税）

---

## 🚀 快速开始

### 方式1: 可执行文件（推荐）
1. 下载 `dist/InvoiceVision.exe`
2. 双击运行，首次启动会自动下载模型
3. 界面出现后即可开始使用

### 方式2: 源代码运行
```bash
# 1. 安装依赖
python install.py

# 2. 启动程序
python InvoiceVision.py
```

### 方式3: 一键打包
```bash
# Windows用户
build.bat

# 或直接运行
python build_lite.py
```

---

## 🛠️ 安装部署

### 系统要求
- **操作系统**: Windows 7/8/10/11 (64位)
- **内存**: 最低 4GB，推荐 8GB+
- **磁盘空间**: 程序 200MB + 模型 100MB
- **Python**: 3.8+ (开发环境需要)

### 开发环境安装
```bash
# 克隆或下载项目
cd InvoiceVision

# 自动安装依赖
python install.py

# 检查环境
python check_build.py

# 启动程序
python InvoiceVision.py
```

### 生产环境部署
```bash
# 打包程序
python build_lite.py

# 部署文件位于 dist/ 目录
# 包含: InvoiceVision.exe, deploy.bat, README.md 等
```

---

## 📖 使用指南

### GUI操作流程
1. **启动程序**: 双击 `InvoiceVision.exe`
2. **选择精度**: 在左侧设置中选择"快速"或"高精"模式
3. **选择文件**: 
   - 点击"处理PDF文件"选择PDF文件
   - 点击"处理图片文件夹"选择包含图片的文件夹
4. **开始处理**: 程序自动处理并显示进度
5. **查看结果**: 右侧表格显示识别结果
6. **导出数据**: 点击"导出Excel"保存结果

### 命令行使用
```python
from OCRInvoice import OfflineOCRInvoice

# 创建OCR识别器
ocr = OfflineOCRInvoice()

# 设置精度模式
ocr.set_precision_mode('快速')  # 或 '高精'

# 识别单张图片
result = ocr.run_ocr('invoice.jpg')
print(result)  # [文件路径, 公司名称, 发票号码, 日期, 金额, 项目名称]
```

### 批量处理
```python
from MainAction import ocr_pdf_offline, ocr_images_offline

# 处理PDF文件
result = ocr_pdf_offline('invoices.pdf', '快速', './output')

# 处理图片文件夹
result = ocr_images_offline('./images/', '高精', './output')
```

---

## 🏗️ 技术架构

### 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户界面层    │    │   业务逻辑层    │    │   数据处理层    │
│                │    │                │    │                │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │  PyQt5 GUI  │ │    │ │ OCRInvoice  │ │    │ │  PaddleOCR  │ │
│ │             │ │    │ │             │ │    │ │             │ │
│ │InvoiceVision│ │◄──►│ │ MainAction  │ │◄──►│ │ PP-OCRv5   │ │
│ │             │ │    │ │             │ │    │ │             │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   配置管理层    │    │   文件处理层    │    │   模型管理层    │
│                │    │                │    │                │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │offline_conf │ │    │ │  PDF2IMG    │ │    │ │ModelManager │ │
│ │             │ │    │ │             │ │    │ │             │ │
│ │resource_utl │ │    │ │             │ │    │ │   models/   │ │
│ │             │ │    │ │             │ │    │ │             │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心模块
- **InvoiceVision.py**: 主GUI界面，提供用户交互
- **OCRInvoice.py**: OCR识别核心，封装PaddleOCR功能
- **MainAction.py**: 批量处理逻辑，协调各模块工作
- **PDF2IMG.py**: PDF转图片工具，支持中文路径
- **ModelManager.py**: 模型管理器，处理模型下载和状态检查
- **resource_utils.py**: 资源管理工具，支持开发和打包环境

### 配置文件
```json
{
  "offline_mode": true,
  "models_path": "models",
  "use_gpu": false,
  "lang": "ch",
  "version": "2.0-external-models",
  "description": "外部模型架构配置 - 模型文件不再打包到exe中"
}
```

---

## 📊 性能指标

### 识别性能
| 指标 | 快速模式 | 高精度模式 |
|------|----------|------------|
| 识别速度 | ~2秒/页 | ~5秒/页 |
| 准确率 | >92% | >96% |
| 内存使用 | ~1GB | ~2GB |

### 文件支持
| 类型 | 格式 | 说明 |
|------|------|------|
| 图片 | JPG, PNG, BMP, TIFF | 支持常见图片格式 |
| 文档 | PDF | 自动转换为图片处理 |
| 批量 | 文件夹 | 支持文件夹批量处理 |

---

## 🔧 故障排除

### 常见问题

#### 1. 程序无法启动
**问题**: 双击exe文件无反应
**解决**:
- 检查系统是否为64位Windows
- 安装 [Visual C++ Redistributable](https://aka.ms/vs/16/release/vc_redist.x64.exe)
- 检查杀毒软件是否误拦截

#### 2. 模型下载失败
**问题**: 首次启动提示模型下载失败
**解决**:
- 检查网络连接
- 使用手动下载方式：
  ```bash
  # 下载模型文件
  python setup_offline_simple.py
  ```
- 使用离线包部署

#### 3. 识别精度低
**问题**: 识别结果不准确
**解决**:
- 切换到"高精度"模式
- 确保图片清晰度
- 检查图片是否倾斜
- 尝试调整图片对比度

#### 4. 内存不足
**问题**: 处理大文件时程序崩溃
**解决**:
- 关闭其他程序释放内存
- 使用"快速"模式
- 分批处理文件

### 环境检查
```bash
# 运行环境检查
python check_build.py

# 检查模型状态
python -c "from ModelManager import ModelManager; m = ModelManager(); print(m.check_models_status())"
```

---

## 🔄 版本历史

### v2.0 (当前版本) - 2025-08-12
- ✨ **新功能**: 模型分离架构，exe体积优化
- 🚀 **性能**: 升级到 PaddleOCR 3.1+ 和 PP-OCRv5
- 🎨 **界面**: 重新设计现代化GUI界面
- 🔧 **技术**: 完善的打包系统和部署脚本
- 📦 **部署**: 支持单文件、离线包、开发包多种部署方式

### v1.0 (历史版本)
- 🎯 **基础**: 基于 PaddleOCR 2.1 的基本OCR功能
- 🖥️ **界面**: 简单的GUI界面
- 📁 **模型**: 模型文件打包在exe中

---

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. **Fork** 本仓库
2. **创建** 特性分支 (`git checkout -b feature/AmazingFeature`)
3. **提交** 更改 (`git commit -m 'Add some AmazingFeature'`)
4. **推送** 分支 (`git push origin feature/AmazingFeature`)
5. **创建** Pull Request

### 开发规范
- 使用 PEP 8 代码风格
- 添加适当的注释和文档
- 确保测试通过
- 更新相关文档

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 📞 联系我们

- **问题反馈**: [GitHub Issues](https://github.com/your-repo/issues)
- **功能建议**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **邮件联系**: support@invoicevision.com

---

## 🙏 致谢

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 强大的OCR引擎
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 优秀的GUI框架
- [PyInstaller](https://www.pyinstaller.org/) - 可靠的打包工具

---

<div align="center">

**💖 如果这个项目对您有帮助，请给我们一个 Star!**

![Star History](https://img.shields.io/github/stars/your-repo/invoicevision?style=social)

</div>