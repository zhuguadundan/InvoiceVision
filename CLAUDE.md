# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an offline Chinese invoice OCR recognition system based on PaddleOCR 3.1+ and PP-OCRv5 models. The system is designed to extract information from Chinese VAT invoices completely offline without any network dependencies.

## Development Commands

### Installation and Setup
```bash
# Install dependencies (recommended)
python install.py

# Manual installation
pip install -r requirements.txt
```

### Running the Application
```bash
# Main GUI application
python InvoiceVision.py

# Direct OCR processing
python OCRInvoice.py
```

### Building Executable
```bash
# Create Windows executable
python build_exe.py

# Generated executable location
./dist/InvoiceVision.exe
```

### Development Tools
```bash
# Debug specific functionality
python debug_invoice_number.py
python detailed_analysis.py
python test_updated_ocr.py
```

## Core Architecture

### Main Components

1. **InvoiceVision.py** - Main PyQt5 GUI application
   - Entry point for user interface
   - Manages threading for OCR operations
   - Handles file selection and progress display

2. **OCRInvoice.py** - Core OCR engine (OfflineOCRInvoice class)
   - Implements PaddleOCR wrapper for offline operation
   - Manages precision modes (快速/高精)
   - Extracts invoice information using regex patterns
   - Loads offline model configuration from `offline_config.json`

3. **MainAction.py** - Batch processing logic
   - `ocr_pdf_offline()` - Process PDF files
   - `ocr_images_offline()` - Process image folders
   - Coordinates between PDF2IMG and OCRInvoice modules

4. **PDF2IMG.py** - PDF to image conversion utility
   - Uses PyMuPDF/fitz for PDF processing
   - Handles Chinese file paths properly
   - Creates organized output directory structure

### Data Flow
```
PDF/Images → PDF2IMG → OCRInvoice → Extracted Invoice Data
```

### Configuration System

- **offline_config.json** - Core model configuration
  ```json
  {
    "offline_mode": true,
    "models": {
      "cls_model_dir": "models/PP-LCNet_x1_0_textline_ori",
      "det_model_dir": "models/PP-OCRv5_server_det", 
      "rec_model_dir": "models/PP-OCRv5_server_rec"
    },
    "use_gpu": false,
    "lang": "ch"
  }
  ```
- **InvoiceVision.spec** - PyInstaller configuration for executable builds
- **build_exe.py** - Enhanced build script with environment checks

### Model Architecture

The system uses PP-OCRv5 models stored locally in `models/`:
- `PP-OCRv5_server_det/` - Text detection
- `PP-OCRv5_server_rec/` - Text recognition  
- `PP-LCNet_x1_0_textline_ori/` - Text line orientation
- Additional models: `PP-LCNet_x1_0_doc_ori/`, `UVDoc/` (when available)

### Threading Model

OCR operations run in separate QThread instances:
- `PDFOCRThread` - For PDF processing
- `ImageOCRThread` - For image folder processing
- Uses Qt signals for progress updates and results

### Invoice Information Extraction

The system extracts these key fields using regex patterns:
- Invoice Code (发票代码) - 10-12 digit numbers
- Invoice Number (发票号码) - 8-digit numbers  
- Date (开票日期) - YYYYMMDD format
- Amount (金额不含税) - Monetary values

### Dependencies

Key dependencies (see requirements.txt):
- paddleocr>=3.1.0
- paddlepaddle>=3.0.0
- PyQt5>=5.15.0
- pymupdf>=1.20.0
- pillow>=8.0.0
- pandas>=1.3.0

## Key Development Patterns

### Offline Architecture
- Complete offline operation with local model storage
- Configuration via JSON files (`offline_config.json`)
- No network dependencies after initial setup

### Threading Pattern
OCR operations use PyQt5 threading with signal/slot communication:
```python
class PDFOCRThread(QThread):
    progress_updated = pyqtSignal(int, str)  # Progress updates
    result_ready = pyqtSignal(str)           # Results
```

### File Processing Flow
1. **PDF Input**: `PDF2IMG.py` converts to images
2. **OCR Processing**: `OCRInvoice.py` extracts text using PaddleOCR
3. **Data Extraction**: Regex patterns extract invoice fields
4. **Output**: Excel/CSV files with structured data

### Build System
- Uses PyInstaller with custom `.spec` configuration
- `build_exe.py` provides automated building with dependency checks
- Includes model files and resources in final executable
- Handles Chinese file paths and Windows-specific requirements

### Resource Management
- `resource_utils.py` handles bundled resource paths
- Supports both development and compiled executable environments
- Manages model file discovery and loading