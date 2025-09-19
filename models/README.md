# 模型目录说明（运行所需与可选资源）

运行必需（默认轻量组合）：
- PP-OCRv5_mobile_det/
- PP-OCRv5_mobile_rec/
- ch_ppocr_mobile_v2.0_cls/

可选/未在当前代码路径中使用（示例/备用）：
- PP-OCRv5_server_det/
- PP-OCRv5_server_rec/
- PP-LCNet_x1_0_doc_ori/
- PP-LCNet_x1_0_textline_ori/
- UVDoc/

建议：
- 如需缩小仓库体积，可将“可选/备用”目录移动到 `models/_extras/` 或从版本库中移除；
- 仅在部署或实验需要时再按需添加；
- `offline_config.json` 与 `resource_utils.py` 默认仅指向“运行必需”的 3 个子目录。
