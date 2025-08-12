# PyInstaller hook for paddleocr - 完全版本，解决所有导入问题
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import sys

# 使用最激进的策略：收集所有PaddleOCR子模块
hiddenimports = []

try:
    print("Collecting all PaddleOCR modules...")
    # 收集所有PaddleOCR子模块，不排除任何
    all_paddleocr_modules = collect_submodules('paddleocr')
    hiddenimports.extend(all_paddleocr_modules)
    print(f"Found {len(all_paddleocr_modules)} PaddleOCR modules")
    
    # 特别确保关键模块被包含
    critical_modules = [
        'paddleocr',
        'paddleocr.paddleocr',
        'paddleocr._models',
        'paddleocr._models.__init__',
        'paddleocr._models.base', 
        'paddleocr._models._image_classification',
        'paddleocr._models.doc_img_orientation_classification',
        'paddleocr.tools',
        'paddleocr.tools.infer',
        'paddleocr.ppocr',
    ]
    
    for module in critical_modules:
        if module not in hiddenimports:
            hiddenimports.append(module)
            
except Exception as e:
    print(f"Warning: Could not collect all PaddleOCR modules: {e}")
    # 回退到手动列表
    hiddenimports = [
        'paddleocr',
        'paddleocr.paddleocr', 
        'paddleocr._models',
        'paddleocr._models.__init__',
        'paddleocr._models.base',
        'paddleocr._models._image_classification',
        'paddleocr._models.doc_img_orientation_classification',
        'paddleocr._models.image_orientation_classification',
        'paddleocr._models.table_master',
        'paddleocr._models.table_structure',
        'paddleocr._models.kie',
        'paddleocr._models.layout_analysis', 
        'paddleocr._models.det',
        'paddleocr._models.rec',
        'paddleocr._models.cls',
        'paddleocr.tools',
        'paddleocr.tools.infer',
        'paddleocr.tools.infer.predict_det',
        'paddleocr.tools.infer.predict_rec',
        'paddleocr.tools.infer.predict_cls',
        'paddleocr.tools.infer.predict_system',
        'paddleocr.tools.infer.utility',
        'paddleocr.ppocr',
        'paddleocr.ppocr.core',
        'paddleocr.ppocr.data',
        'paddleocr.ppocr.losses',
        'paddleocr.ppocr.metrics',
        'paddleocr.ppocr.modeling', 
        'paddleocr.ppocr.optimizer',
        'paddleocr.ppocr.postprocess',
        'paddleocr.ppocr.utils',
    ]

# 收集所有数据文件
datas = []
try:
    paddleocr_data = collect_data_files('paddleocr')
    datas.extend(paddleocr_data)
    print(f"Found {len(paddleocr_data)} data files")
except Exception as e:
    print(f"Warning: Could not collect PaddleOCR data files: {e}")

# 不排除任何模块，确保完整性
excludedimports = []

print(f"PaddleOCR hook: Including {len(hiddenimports)} modules")