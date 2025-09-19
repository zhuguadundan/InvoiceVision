# InvoiceVision - 桌面版（GUI）

基于 PaddleOCR 的离线中文发票OCR识别器，提供 Windows 桌面图形界面，支持批量处理与 Excel 导出。

## 快速开始（GUI）

1) 解压部署包，双击 `InvoiceVision.bat` 启动；或源码方式：

```bash
python install.py        # 安装依赖（首次）
python InvoiceVision.py  # 启动GUI
```

2) 首次启动如缺少模型，按界面提示打开“模型配置”复制模型，或按下文链接下载后解压到 `models/`。

## 系统要求

- Windows 7 x64 或更高版本
- 内存 2GB+（建议 4GB）

## 使用步骤

- 选择要处理的 PDF 或图片文件夹
- 开始处理，识别结果在界面汇总，可导出为 Excel

## 故障排除

- 启动失败：确认解压路径无中文空格；以管理员身份运行
- 模型缺失：通过“模型配置”复制模型，或按下文链接下载后解压到 `models/`

## 常见模型目录结构与获取

默认使用 PP-OCRv5 mobile 轻量组合（CPU 友好）：

```
models/
├─ PP-OCRv5_mobile_det/
│  ├─ inference.json   或  inference.pdmodel
│  └─ inference.pdiparams
├─ PP-OCRv5_mobile_rec/
│  ├─ inference.json   或  inference.pdmodel
│  └─ inference.pdiparams
└─ ch_ppocr_mobile_v2.0_cls/
   ├─ inference.json   或  inference.pdmodel
   └─ inference.pdiparams
```

获取方式（任选其一）：
- 方式A｜复制现有模型：从已配置好的电脑上，拷贝上述三个目录到本项目 `models/` 下。
- 方式B｜手动下载官方模型并解压到 `models/`：
  - 识别（rec）：PP-OCRv5_mobile_rec_infer.tar
    - https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv5_mobile_rec_infer.tar
  - 分类（cls）：ch_ppocr_mobile_v2.0_cls_infer.tar
    - https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar
  - 检测（det）：优先 PP-OCRv5_mobile_det；如暂不可用，可使用 PP-OCRv4_mobile_det_infer.tar 作为替代
    - https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-OCRv4_mobile_det_infer.tar

解压与校验：
- 将 tar 解压到 `models/` 下，目录名保持与上例一致；若解压后出现 `*_infer/` 子目录，请将其中文件上移到父目录。
- 每个目录至少包含 `inference.pdiparams` 和 `inference.json`（或旧版 `inference.pdmodel`）。

配置一致性：
- `offline_config.json` 中的 `models.det_model_dir/rec_model_dir/cls_model_dir` 需与实际目录一致；默认已指向上述三个目录。
- 识别慢：老旧电脑可保持默认“轻量模型”，避免使用大型模型

## 许可证

MIT 许可证

## 致谢

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR 引擎
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
