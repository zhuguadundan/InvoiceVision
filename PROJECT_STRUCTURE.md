# InvoiceVision 项目结构说明

## 项目概述
InvoiceVision 是一个基于 PaddleOCR 3.1+ 的离线中文发票 OCR 识别系统，支持完全离线运行和模型分离架构。

## 📁 目录结构

```
InvoiceVision/
├── 📄 核心程序文件
│   ├── InvoiceVision.py           # 主GUI程序
│   ├── OCRInvoice.py              # OCR核心引擎
│   ├── MainAction.py              # 批量处理逻辑
│   ├── PDF2IMG.py                 # PDF转图片工具
│   ├── ModelManager.py            # 模型管理器
│   └── resource_utils.py          # 资源管理工具
│
├── 📦 打包和部署
│   ├── InvoiceVision.spec         # PyInstaller配置
│   ├── build_lite.py             # 打包脚本
│   ├── build.bat                  # 一键打包批处理
│   ├── check_build.py             # 打包前检查
│   ├── version.txt                # 版本信息
│   └── version_info.txt           # Windows版本信息
│
├── 🔧 配置和依赖
│   ├── offline_config.json        # 离线模式配置
│   ├── requirements.txt           # Python依赖列表
│   ├── install.py                 # 安装脚本
│   └── setup_offline_simple.py    # 离线设置脚本
│
├── 🎯 PyInstaller Hooks
│   └── pyinstaller_hooks/
│       ├── hook-jaraco.py         # jaraco依赖hook
│       ├── hook-paddleocr.py      # PaddleOCR hook
│       ├── hook-paddlex.py        # PaddleX hook
│       └── hook-pkg_resources.py  # pkg_resources hook
│
├── 🧠 模型文件
│   └── models/                    # OCR模型文件目录
│       ├── PP-OCRv5_server_det/   # 文本检测模型
│       ├── PP-OCRv5_server_rec/   # 文本识别模型
│       ├── PP-LCNet_x1_0_textline_ori/  # 文本方向模型
│       ├── PP-LCNet_x1_0_doc_ori/       # 文档方向模型
│       └── UVDoc/                  # 文档分析模型（可选）
│
├── 📦 构建输出
│   └── dist/                      # 打包输出目录
│       ├── InvoiceVision.exe      # 可执行文件
│       ├── README.md               # 使用说明
│       ├── deploy.bat              # 部署脚本
│       ├── LICENSE                 # 许可证
│       ├── requirements.txt        # 依赖列表
│       └── offline_config.json     # 配置文件
│
├── 📚 文档
│   ├── README.md                  # 项目主页
│   ├── CLAUDE.md                  # Claude Code指导
│   ├── BUILD_SUMMARY.md           # 打包总结
│   ├── LICENSE                    # 开源许可证
│   └── 使用说明.md                # 中文使用说明
│
└── 📄 其他
    └── .gitignore                 # Git忽略文件
```

## 🔍 核心文件说明

### 程序入口
- **InvoiceVision.py**: 主程序，提供PyQt5 GUI界面
- **OCRInvoice.py**: OCR识别核心，封装PaddleOCR功能
- **MainAction.py**: 批量处理逻辑，支持PDF和图片处理

### 配置管理
- **offline_config.json**: 核心配置文件，控制离线模式和行为
- **resource_utils.py**: 资源文件管理，支持开发环境和打包环境

### 模型系统
- **ModelManager.py**: 模型文件管理，支持下载和状态检查
- **models/**: 模型文件目录，采用分离架构

### 打包系统
- **InvoiceVision.spec**: PyInstaller配置，模型分离架构
- **build_lite.py**: 智能打包脚本，包含环境检查
- **check_build.py**: 打包前环境验证

## 🚀 快速开始

### 开发环境
```bash
# 1. 安装依赖
python install.py

# 2. 运行程序
python InvoiceVision.py

# 3. 打包前检查
python check_build.py

# 4. 打包程序
python build_lite.py
```

### 一键操作
```bash
# Windows用户
build.bat

# 或直接运行
python build_lite.py
```

## 🎯 项目特点

### ✅ 核心功能
- **离线OCR识别**: 完全离线运行，无需网络依赖
- **多格式支持**: 支持PDF和图片格式
- **批量处理**: 支持文件和文件夹批量处理
- **GUI界面**: 现代化PyQt5界面
- **Excel导出**: 识别结果导出为Excel格式

### ✅ 技术特点
- **模型分离**: exe文件体积小，模型独立管理
- **自动下载**: 首次运行自动下载模型文件
- **版本管理**: 支持模型版本更新和管理
- **多平台**: 支持Windows 64位系统
- **中文支持**: 完整中文界面和文件名支持

### ✅ 开发友好
- **完整文档**: 详细的使用说明和开发指南
- **环境检查**: 自动检查开发环境依赖
- **错误处理**: 完善的错误提示和日志
- **测试支持**: 提供多种测试和调试工具

## 📦 部署方式

### 方式1: 单文件部署
- 只需`InvoiceVision.exe`
- 首次运行自动下载模型
- 适合个人用户

### 方式2: 离线包部署
- 完整的`dist/`目录
- 包含所有必要文件
- 适合企业部署

### 方式3: 开发部署
- 完整源代码
- 支持自定义配置
- 适合开发者

## 🔧 系统要求

### 最低要求
- Windows 7/8/10/11 (64位)
- 内存: 4GB
- 磁盘: 500MB (程序+模型)

### 推荐配置
- Windows 10/11 (64位)
- 内存: 8GB+
- 磁盘: 1GB+
- 网络: 首次运行需要

## 📝 版本信息

- **当前版本**: 2.0-模型分离版
- **Python版本**: 3.8+
- **PyInstaller**: 6.15.0
- **PaddleOCR**: 3.1.0+
- **发布时间**: 2025-08-12

## 📄 许可证

本项目采用开源许可证，详见 [LICENSE](LICENSE) 文件。

## 📞 技术支持

如有问题，请查看：
1. 使用说明文档
2. 项目主页 README.md
3. CLAUDE.md 开发指南
4. BUILD_SUMMARY.md 打包总结

---
**InvoiceVision** - 智能发票OCR识别系统