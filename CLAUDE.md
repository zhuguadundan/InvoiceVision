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

### Building and Deployment
```bash
# Environment check before building
python check_build.py

# Build Windows executable (full)
python build_exe.py

# Build lightweight executable
python build_lite.py

# One-click build script (Windows)
build.bat

# Deploy external models
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

### Main Components

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

Core dependencies (requirements.txt):
- paddleocr>=3.1.0 - OCR engine
- paddlepaddle>=3.0.0 - ML framework
- PyQt5>=5.15.0 - GUI framework
- pymupdf>=1.20.0 - PDF processing
- pillow>=8.0.0, opencv-contrib-python>=4.10.0 - Image processing
- pandas>=1.3.0, numpy>=1.24.0 - Data handling
- pyyaml>=6.0, requests>=2.25.0 - Configuration and networking
- typing-extensions>=4.12.0 - Type hints

## Key Development Patterns

### External Model Management
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