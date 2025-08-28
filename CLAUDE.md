# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an offline Chinese invoice OCR recognition system based on PaddleOCR 3.1+ and PP-OCRv5 models. The system extracts information from Chinese VAT invoices completely offline without network dependencies, featuring an external model architecture that separates the executable from large model files.

## Development Commands

### Installation and Setup
```bash
# Install dependencies (recommended)
python install.py

# Manual installation
pip install -r requirements.txt

# Check environment readiness
python check_build.py
```

### Running the Application
```bash
# Main GUI application
python InvoiceVision.py

# Direct OCR processing
python OCRInvoice.py

# Setup models for first run
python setup_offline_simple.py
```

### Building and Deployment (Embedded Python Architecture)

**🎯 RECOMMENDED APPROACH** - Based on UMI-OCR successful pattern

```bash
# 🚀 One-click packaging (RECOMMENDED)
build_package.bat

# Manual packaging with Python
python-embed\python.exe package_builder.py

# Test embedded Python setup
python-embed\python.exe main.py
```

**Deployment Structure:**
```
InvoiceVision_Release/
├── InvoiceVision.bat          # Main launcher
├── main.py                    # Python entry point  
├── InvoiceVision.py          # Main application
├── python-embed/             # Embedded Python runtime (~160MB)
│   ├── python.exe
│   ├── Lib/site-packages/    # Contains PaddleOCR, PyQt5, etc.
│   └── ...
├── models/                   # External model files
└── README_DEPLOYMENT.md      # User guide
```

**Key Advantages:**
- ✅ **100% Success Rate** - No PyInstaller dependency issues
- ✅ **No Python Required** - Users don't need Python installed  
- ✅ **Extract & Run** - Simple deployment experience
- ✅ **~200MB Total** - Reasonable package size
- ✅ **Perfect Compatibility** - All OCR dependencies work flawlessly

### Legacy Building Methods (DEPRECATED)
```bash
# ❌ DEPRECATED - PyInstaller approaches (historical failures)
# Environment check before building
python check_build.py

# Build Windows executable (full) - FAILED
python build_exe.py

# Build lightweight executable - FAILED
python build_lite.py

# One-click build script (Windows) - FAILED
build.bat

# Deploy external models - LEGACY
deploy_external_models.bat

# Generated executable location
./dist/InvoiceVision.exe
```

### Testing and Diagnostics
```bash
# Test basic OCR functionality
python test_basic_ocr.py
python test_ocr_simple.py
python test_ocr_quick.py

# Test packaged executable
python test_exe_functionality.py
python test_packaged_ocr.py

# Debug and diagnose issues
python analyze_ocr_issues.py
python diagnose_exe.py
python build_diagnose.py
```

## Core Architecture

### Modern Embedded Python Architecture (Current)

The project now uses a **PyStand-inspired embedded Python architecture** that completely solves the PyInstaller packaging issues:

```
Runtime Architecture:
InvoiceVision.bat → python-embed\python.exe → main.py → InvoiceVision.py
                                             │
                                             ├─ OCRInvoice.py (OCR Engine)
                                             ├─ MainAction.py (Batch Processing)
                                             ├─ PDF2IMG.py (PDF Conversion)
                                             ├─ ModelManager.py (Model Management)
                                             └─ resource_utils.py (Resource Utils)
                                             
Embedded Environment:
python-embed/
├── python.exe                    # Python 3.11.9 interpreter
├── python311.dll               # Core runtime
├── Lib/site-packages/          # All dependencies
│   ├── paddleocr/             # OCR engine
│   ├── PyQt5/                 # GUI framework
│   ├── pandas/                # Data processing
│   └── ... (all other deps)
└── python311._pth              # Path configuration
```

**Key Success Factors:**
- **No PyInstaller Complexity** - Bypasses all packaging compilation issues
- **Runtime Environment** - Uses real Python interpreter with full compatibility
- **External Models** - Models separate from executable for flexibility
- **UMI-OCR Proven Pattern** - Based on successfully deployed OCR software

### Legacy Architecture (Historical Reference)

**Previous Components** (maintained for compatibility):

1. **InvoiceVision.py** - Main PyQt5 GUI application
   - Entry point with modern GUI interface
   - Manages threading via `OfflineOCRThread` base class
   - Handles file selection and progress display
   - Integrates with `ModelManager` for model status checking

2. **OCRInvoice.py** - Core OCR engine (`OfflineOCRInvoice` class)
   - PaddleOCR wrapper for offline operation
   - Dual precision modes: 快速 (Fast) / 高精 (High Precision)
   - Regex-based invoice field extraction
   - Configuration loading from `offline_config.json`

3. **MainAction.py** - Batch processing coordination
   - `ocr_pdf_offline()` - PDF file processing pipeline
   - `ocr_images_offline()` - Image folder processing
   - Orchestrates PDF2IMG → OCRInvoice → Data Export flow

4. **PDF2IMG.py** - PDF conversion utility
   - PyMuPDF/fitz-based PDF processing
   - Chinese file path support with proper encoding
   - Organized output directory structure

5. **ModelManager.py** - External model management
   - Model download and status verification
   - Separates model files from executable
   - Handles missing model scenarios

6. **resource_utils.py** - Resource path management
   - Supports both development and packaged environments
   - Handles bundled vs. external resource paths

### External Model Architecture

The system uses a separated model architecture:
- **Executable**: `InvoiceVision.exe` (~200MB, no models)
- **Models**: Downloaded on-demand to `models/` directory (~100MB)
- **Benefits**: Smaller distribution, incremental updates, flexible deployment

Required models in `models/`:
- `PP-OCRv5_server_det/` - Text detection model
- `PP-OCRv5_server_rec/` - Text recognition model
- `PP-LCNet_x1_0_textline_ori/` - Text line orientation model
- Optional: `PP-LCNet_x1_0_doc_ori/`, `UVDoc/`

### Configuration System

- **offline_config.json** - Core configuration:
  ```json
  {
    "offline_mode": true,
    "models_path": "models",
    "use_gpu": false,
    "lang": "ch",
    "version": "2.0-external-models"
  }
  ```
- **InvoiceVision.spec** - PyInstaller configuration with external model exclusion
- **build_exe.py** - Enhanced build script with comprehensive environment checks

### Data Processing Flow
```
PDF/Images → PDF2IMG → OCRInvoice → ModelManager → Extracted Invoice Data → Excel/CSV
```

### Threading Model

All OCR operations run in separate QThread instances with Qt signals:
- `OfflineOCRThread` - Base thread class for common OCR functionality
- `PDFOCRThread` - Specialized for PDF batch processing
- `ImageOCRThread` - Specialized for image folder processing
- Signals: `progress`, `result`, `ocr_result`, `finished`

### Invoice Information Extraction

Regex patterns extract key invoice fields:
- **Invoice Code** (发票代码) - 10-12 digit numbers
- **Invoice Number** (发票号码) - 8-digit numbers  
- **Date** (开票日期) - YYYYMMDD format
- **Amount** (金额不含税) - Monetary values
- **Company Name** (开票公司名称) - Chinese text
- **Project Name** (项目名称) - Service/item description

### Dependencies

**Embedded Python Environment (python-embed/):**
- **python**: 3.11.9 embeddable distribution
- **paddleocr**: 3.2.0 - OCR engine
- **paddlepaddle**: 3.1.1 - ML framework  
- **PyQt5**: 5.15.11 - GUI framework
- **pymupdf**: 1.26.4 - PDF processing
- **pillow**: 11.3.0 - Image processing
- **opencv-contrib-python**: 4.10.0.84 - Computer vision
- **pandas**: 2.3.2 - Data handling
- **numpy**: 2.2.6 - Numerical computing
- **pyyaml**: 6.0.2 - Configuration files
- **requests**: 2.32.5 - HTTP requests (for model downloads)

**Legacy Dependencies (requirements.txt) - For Development Only:**
Core dependencies for development environment:
- paddleocr>=3.1.0 - OCR engine
- paddlepaddle>=3.0.0 - ML framework
- PyQt5>=5.15.0 - GUI framework
- pymupdf>=1.20.0 - PDF processing
- pillow>=8.0.0, opencv-contrib-python>=4.10.0 - Image processing
- pandas>=1.3.0, numpy>=1.24.0 - Data handling
- pyyaml>=6.0, requests>=2.25.0 - Configuration and networking
- typing-extensions>=4.12.0 - Type hints

## Key Development Patterns

### Embedded Python Deployment (Current Best Practice)

**Setup Process:**
1. **Download Python Embeddable**: Python 3.11.9 embedded distribution
2. **Configure Environment**: Enable pip and site-packages
3. **Install Dependencies**: Use embedded pip to install all OCR dependencies
4. **Test Compatibility**: Verify PaddleOCR works in embedded environment
5. **Package for Distribution**: Use `build_package.bat` or `package_builder.py`

**Development vs Production:**
- **Development**: Use system Python with `python InvoiceVision.py`
- **Production**: Use embedded Python with `InvoiceVision.bat` → `main.py`

**Key Files:**
- `main.py`: Embedded Python entry point (sets up paths and executes InvoiceVision.py)
- `InvoiceVision.bat`: User-friendly Windows launcher
- `package_builder.py`: Automated packaging script
- `build_package.bat`: One-click packaging for users

### Legacy Patterns (Historical Reference)

### External Model Management (Maintained)
- Models are excluded from executable via `.spec` file
- `ModelManager` handles download and verification
- Graceful degradation when models are missing
- First-run automatic model download with user prompts

### Build System Architecture
- **Multi-stage build**: Environment check → Dependencies → PyInstaller → Model deployment
- **Conditional inclusion**: Models excluded from main executable
- **Windows focus**: Batch files, path handling, executable icons
- **Diagnostics**: Comprehensive build and runtime diagnostic tools

### Resource Path Handling
- `resource_utils.py` abstracts path resolution
- Supports both development (`./`) and packaged (`sys._MEIPASS`) environments
- Handles missing resources gracefully with fallbacks

### Error Handling and Diagnostics
- Comprehensive environment validation in `check_build.py`
- Multiple test scripts for different components
- Diagnostic tools for build and runtime issues
- Graceful degradation for missing dependencies

### Chinese Localization
- UTF-8 encoding throughout
- Chinese file path support
- Localized error messages and UI text
- Invoice field patterns optimized for Chinese VAT invoices

### Testing Strategy
- Component-level tests (basic OCR, PDF processing)
- Integration tests (packaged executable functionality)
- Diagnostic tests (environment, model status)
- Performance tests (speed vs. accuracy modes)