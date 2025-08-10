# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an offline Chinese invoice OCR recognition system based on PaddleOCR 3.1+ and PP-OCRv5 models. The system is designed to extract information from Chinese VAT invoices completely offline without any network dependencies.

## Development Commands

### Installation and Setup
```bash
# Install dependencies
python install.py
# or manually:
pip install -r requirements.txt

# Set up offline models (if needed)
python setup_offline_simple.py
```

### Running the Application
```bash
# Main GUI application (recommended)
python InvoiceVision.py

# Direct OCR processing (programmatic use)
python OCRInvoice.py
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

- **offline_config.json** - Offline model configuration
  - Points to local PP-OCRv5 model directories
  - Defines GPU usage and language settings
  - Models located in `models/` directory (209.4MB total)

### Model Architecture

The system uses 5 PP-OCRv5 models stored locally:
- `PP-OCRv5_server_det/` - Text detection
- `PP-OCRv5_server_rec/` - Text recognition  
- `PP-LCNet_x1_0_textline_ori/` - Text line orientation
- `PP-LCNet_x1_0_doc_ori/` - Document orientation
- `UVDoc/` - Document unwarping

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

## Development Notes

- The system is designed for complete offline operation
- All models are stored locally in the `models/` directory
- Configuration uses JSON files rather than command-line arguments
- GUI uses PyQt5 threading to prevent UI blocking during OCR operations
- Error handling includes user-friendly Chinese messages
- The system has been streamlined to a single version (offline-only)