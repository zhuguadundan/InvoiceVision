#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
InvoiceVision Web Interface
现代化的Web界面，支持文件上传、OCR处理、实时进度和结果展示
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_socketio import SocketIO, emit
import os
import json
import threading
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO
import zipfile
import time
import sys
import traceback
import secrets

# 导入核心OCR模块
try:
    from MainAction import ocr_pdf_offline, ocr_images_offline
    from OCRInvoice import OfflineOCRInvoice
    from ModelManager import ModelManager
    from PDF2IMG import pdf2img
except ImportError as e:
    print(f"Warning: 无法导入核心模块: {e}")
    # 创建兼容的存根类
    class MainAction:
        @staticmethod
        def ocr_pdf_offline(*args, **kwargs):
            return {"error": "核心OCR模块未可用"}
    
    class OfflineOCRInvoice:
        pass
    
    class ModelManager:
        def check_models_status(self):
            return "missing", "模型管理器不可用"

app = Flask(__name__)
# 从环境变量加载密钥，默认生成随机密钥（更安全）
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# 在容器以外环境下提供目录回退（也支持通过环境变量覆盖）
def _resolve_dir(env_key, default_container_path, fallback_name):
    p = os.environ.get(env_key, default_container_path)
    # 若路径不存在，则使用当前工作目录下的回退目录
    if not os.path.isabs(p) or (os.path.isabs(p) and not os.path.exists(p)):
        p = os.path.join(os.getcwd(), fallback_name)
    os.makedirs(p, exist_ok=True)
    return p

app.config['UPLOAD_FOLDER'] = _resolve_dir('UPLOAD_DIR', '/app/input', 'input')
app.config['RESULTS_FOLDER'] = _resolve_dir('RESULTS_DIR', '/app/output', 'output')
app.config['MODELS_FOLDER'] = _resolve_dir('MODELS_DIR', '/app/models', 'models')

# 初始化WebSocket（支持通过环境变量切换异步模式：threading/eventlet/gevent）
ASYNC_MODE = os.environ.get('SOCKETIO_ASYNC_MODE', 'threading').lower()
socketio = SocketIO(app, cors_allowed_origins=os.environ.get('CORS_ORIGINS', '*'), async_mode=ASYNC_MODE)

# 添加静态文件路由处理
@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    return send_from_directory('static', filename)

# 全局变量
active_tasks = {}  # 存储活动任务
active_tasks_lock = threading.Lock()
model_manager = ModelManager()

ALLOWED_EXTENSIONS = {
    'pdf': ['pdf'],
    'image': ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff']
}

def allowed_file(filename, file_type='all'):
    """检查文件扩展名是否允许"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'pdf':
        return ext in ALLOWED_EXTENSIONS['pdf']
    elif file_type == 'image':
        return ext in ALLOWED_EXTENSIONS['image']
    else:  # all
        all_exts = set()
        for exts in ALLOWED_EXTENSIONS.values():
            all_exts.update(exts)
        return ext in all_exts

def emit_progress(task_id, message, progress=None, data=None):
    """发送进度更新到前端"""
    socketio.emit('progress_update', {
        'task_id': task_id,
        'message': message,
        'progress': progress,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })

class OCRTask:
    """OCR任务处理器"""
    
    def __init__(self, task_id, task_type, files, precision_mode='快速'):
        self.task_id = task_id
        self.task_type = task_type  # 'pdf' 或 'images'
        self.files = files
        self.precision_mode = precision_mode
        self.status = 'pending'
        self.results = []
        self.error = None
        self.start_time = None
        self.end_time = None
    
    def run(self):
        """执行OCR任务"""
        self.status = 'running'
        self.start_time = datetime.now()
        
        try:
            emit_progress(self.task_id, f"🚀 开始{self.task_type}处理...", 10)
            
            if self.task_type == 'pdf':
                self._process_pdf_files()
            else:
                self._process_image_files()
                
            self.status = 'completed'
            emit_progress(self.task_id, "✅ 所有文件处理完成!", 100, {
                'results': self.results,
                'task_id': self.task_id
            })
            
        except Exception as e:
            self.status = 'error'
            self.error = str(e)
            emit_progress(self.task_id, f"❌ 处理出错: {str(e)}", 0, {'error': str(e)})
            print(f"OCR任务错误: {e}")
            traceback.print_exc()
        
        finally:
            self.end_time = datetime.now()
    
    def _process_pdf_files(self):
        """处理PDF文件"""
        total_files = len(self.files)
        
        for i, file_path in enumerate(self.files):
            try:
                progress = 20 + (i / total_files) * 70
                emit_progress(
                    self.task_id, 
                    f"📄 处理PDF文件 ({i+1}/{total_files}): {os.path.basename(file_path)}", 
                    progress
                )
                
                # 调用核心OCR处理函数
                result = ocr_pdf_offline(
                    file_path, 
                    self.precision_mode, 
                    app.config['RESULTS_FOLDER']
                )
                
                if result and 'invoice_data' in result:
                    invoice_data = result['invoice_data']
                    if isinstance(invoice_data, list):
                        self.results.extend(invoice_data)
                    else:
                        self.results.append(invoice_data)
                
                time.sleep(0.1)  # 短暂延迟以显示进度
                
            except Exception as e:
                error_msg = f"处理文件 {os.path.basename(file_path)} 失败: {str(e)}"
                emit_progress(self.task_id, error_msg, progress)
                print(error_msg)
    
    def _process_image_files(self):
        """处理图片文件"""
        # 创建临时目录存放图片
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # 复制文件到临时目录
            for file_path in self.files:
                import shutil
                shutil.copy2(file_path, temp_dir)
            
            emit_progress(self.task_id, f"🖼️ 处理 {len(self.files)} 个图片文件...", 30)
            
            # 调用核心图片处理函数
            result = ocr_images_offline(
                temp_dir,
                self.precision_mode,
                app.config['RESULTS_FOLDER']
            )
            
            if result and 'invoice_data' in result:
                invoice_data = result['invoice_data']
                if isinstance(invoice_data, list):
                    self.results.extend(invoice_data)
                else:
                    self.results.append(invoice_data)

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API状态检查"""
    try:
        # 清理过期任务
        cleanup_tasks()
        # 检查模型状态
        status, message = model_manager.check_models_status()
        
        # 检查离线配置
        offline_config = {}
        config_file = "/app/offline_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                offline_config = json.load(f)
        
        return jsonify({
            'status': 'ok',
            'model_status': status,
            'model_message': message,
            'offline_mode': offline_config.get('offline_mode', True),
            'version': offline_config.get('version', '2.0-web'),
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'results_folder': app.config['RESULTS_FOLDER'],
            'active_tasks': len(active_tasks)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """文件上传API"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': '没有文件被上传'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        uploaded_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # 添加时间戳避免冲突
                name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{name}_{timestamp}{ext}"
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                uploaded_files.append({
                    'original_name': file.filename,
                    'saved_name': unique_filename,
                    'file_path': file_path,
                    'file_size': os.path.getsize(file_path),
                    'file_type': 'pdf' if filename.lower().endswith('.pdf') else 'image'
                })
        
        return jsonify({
            'message': f'成功上传 {len(uploaded_files)} 个文件',
            'files': uploaded_files
        })
        
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/process', methods=['POST'])
def api_process():
    """启动OCR处理"""
    try:
        data = request.get_json()
        
        if not data or 'files' not in data:
            return jsonify({'error': '缺少文件信息'}), 400
        
        files = data['files']
        precision_mode = data.get('precision_mode', '快速')
        
        if not files:
            return jsonify({'error': '没有要处理的文件'}), 400
        
        # 创建任务ID
        task_id = str(uuid.uuid4())
        
        # 按文件类型分组
        pdf_files = [f['file_path'] for f in files if f['file_type'] == 'pdf']
        image_files = [f['file_path'] for f in files if f['file_type'] == 'image']
        
        # 创建任务列表
        tasks = []
        if pdf_files:
            tasks.append(OCRTask(f"{task_id}_pdf", 'pdf', pdf_files, precision_mode))
        if image_files:
            tasks.append(OCRTask(f"{task_id}_images", 'images', image_files, precision_mode))
        
        if not tasks:
            return jsonify({'error': '没有有效的文件可处理'}), 400
        
        # 存储任务
        with active_tasks_lock:
            active_tasks[task_id] = {
                'tasks': tasks,
                'status': 'starting',
                'results': [],
                'created_at': datetime.now().isoformat()
            }
        
        # 在后台线程中执行任务
        def run_tasks():
            try:
                all_results = []
                for task in tasks:
                    with active_tasks_lock:
                        active_tasks[task_id]['status'] = 'running'
                    task.run()
                    if task.results:
                        all_results.extend(task.results)
                
                # 保存结果
                with active_tasks_lock:
                    active_tasks[task_id]['results'] = all_results
                    active_tasks[task_id]['status'] = 'completed'
                
                # 发送最终完成通知到前端
                emit_progress(task_id, f"🎉 处理完成！共识别 {len(all_results)} 条发票信息", 100, {
                    'results': all_results,
                    'task_id': task_id,
                    'completed': True
                })
                
                # 生成Excel文件
                if all_results:
                    excel_path = save_results_to_excel(all_results, task_id)
                    with active_tasks_lock:
                        active_tasks[task_id]['excel_path'] = excel_path
                
            except Exception as e:
                with active_tasks_lock:
                    active_tasks[task_id]['status'] = 'error'
                    active_tasks[task_id]['error'] = str(e)
                emit_progress(task_id, f"❌ 任务执行失败: {str(e)}", 0, {'error': str(e)})
            finally:
                # 任务完成后尝试清理过期任务
                cleanup_tasks()
        
        threading.Thread(target=run_tasks, daemon=True).start()
        
        return jsonify({
            'message': '处理任务已启动',
            'task_id': task_id,
            'files_count': len(files)
        })
        
    except Exception as e:
        return jsonify({'error': f'启动处理失败: {str(e)}'}), 500

@app.route('/api/task/<task_id>')
def api_task_status(task_id):
    """获取任务状态"""
    # 周期性清理过期任务
    cleanup_tasks()
    if task_id not in active_tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task_info = active_tasks[task_id]
    
    return jsonify({
        'task_id': task_id,
        'status': task_info['status'],
        'results_count': len(task_info.get('results', [])),
        'results': task_info.get('results', []),
        'excel_available': 'excel_path' in task_info,
        'created_at': task_info['created_at'],
        'error': task_info.get('error')
    })

@app.route('/api/results/<task_id>/excel')
def api_download_excel(task_id):
    """下载Excel结果文件"""
    if task_id not in active_tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task_info = active_tasks[task_id]
    if 'excel_path' not in task_info:
        return jsonify({'error': 'Excel文件不存在'}), 404
    
    return send_file(
        task_info['excel_path'],
        as_attachment=True,
        download_name=f'发票识别结果_{task_id}.xlsx'
    )

@app.route('/api/results/all/excel', methods=['POST'])
def api_download_all_excel():
    """下载所有历史结果Excel文件"""
    try:
        data = request.get_json()
        results = data.get('results', [])
        
        if not results:
            return jsonify({'error': '没有结果数据'}), 400
        
        # 生成Excel文件
        excel_path = save_results_to_excel(results, 'all_history')
        
        if not excel_path or not os.path.exists(excel_path):
            return jsonify({'error': 'Excel文件生成失败'}), 500
        
        return send_file(
            excel_path,
            as_attachment=True,
            download_name=f'发票识别历史结果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': f'生成Excel失败: {str(e)}'}), 500

@app.route('/api/results/all/json', methods=['POST'])
def api_download_all_json():
    """下载所有历史结果JSON文件"""
    try:
        data = request.get_json()
        results = data.get('results', [])
        
        if not results:
            return jsonify({'error': '没有结果数据'}), 400
        
        # 创建JSON文件
        json_data = {
            'exported_at': datetime.now().isoformat(),
            'total_invoices': len(results),
            'invoices': results
        }
        
        json_bytes = json.dumps(json_data, ensure_ascii=False, indent=2).encode('utf-8')
        json_io = BytesIO(json_bytes)
        
        return send_file(
            json_io,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'发票识别历史结果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        
    except Exception as e:
        return jsonify({'error': f'生成JSON失败: {str(e)}'}), 500

@app.route('/api/results/<task_id>/json')
def api_download_json(task_id):
    """下载JSON结果文件"""
    if task_id not in active_tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task_info = active_tasks[task_id]
    results = task_info.get('results', [])
    
    # 创建JSON文件
    json_data = {
        'task_id': task_id,
        'processed_at': datetime.now().isoformat(),
        'total_invoices': len(results),
        'invoices': results
    }
    
    json_bytes = json.dumps(json_data, ensure_ascii=False, indent=2).encode('utf-8')
    json_io = BytesIO(json_bytes)
    
    return send_file(
        json_io,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'发票识别结果_{task_id}.json'
    )

@app.route('/api/models/status')
def api_models_status():
    """获取模型状态"""
    try:
        status, message = model_manager.check_models_status()
        
        # 获取模型详细信息
        models_info = {}
        models_dir = app.config['MODELS_FOLDER']
        
        if os.path.exists(models_dir):
            for item in os.listdir(models_dir):
                item_path = os.path.join(models_dir, item)
                if os.path.isdir(item_path):
                    # 计算目录大小
                    total_size = 0
                    for root, dirs, files in os.walk(item_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)
                    
                    models_info[item] = {
                        'size_mb': round(total_size / (1024 * 1024), 2),
                        'files_count': len([f for _, _, files in os.walk(item_path) for f in files])
                    }
        
        return jsonify({
            'status': status,
            'message': message,
            'models': models_info,
            'models_path': models_dir
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/clear')
def api_clear_files():
    """清理上传的文件"""
    try:
        import shutil
        
        # 清理上传目录
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # 清理结果目录（可选）
        cleared_files = 0
        if os.path.exists(app.config['RESULTS_FOLDER']):
            for file in os.listdir(app.config['RESULTS_FOLDER']):
                if file.endswith(('.xlsx', '.json')):
                    os.remove(os.path.join(app.config['RESULTS_FOLDER'], file))
                    cleared_files += 1
        
        return jsonify({
            'message': f'已清理上传文件和 {cleared_files} 个结果文件',
            'cleared_count': cleared_files
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def cleanup_tasks():
    """清理过期任务，默认 TTL 30 分钟（仅清理已完成/错误的任务）"""
    try:
        ttl_minutes = int(os.environ.get('TASK_TTL_MINUTES', '30'))
    except Exception:
        ttl_minutes = 30
    now = datetime.now()
    to_delete = []
    with active_tasks_lock:
        for tid, info in list(active_tasks.items()):
            status = info.get('status')
            created = info.get('created_at')
            if not created:
                continue
            try:
                created_dt = datetime.fromisoformat(created)
            except Exception:
                continue
            age_minutes = (now - created_dt).total_seconds() / 60.0
            if status in ('completed', 'error') and age_minutes > ttl_minutes:
                to_delete.append(tid)
        for tid in to_delete:
            del active_tasks[tid]
    if to_delete:
        print(f"清理过期任务 {len(to_delete)} 个: {to_delete}")


def save_results_to_excel(results, task_id):
    """保存结果到Excel文件"""
    try:
        if not results:
            return None
        
        # 转换结果为DataFrame
        data_list = []
        for result in results:
            if isinstance(result, list) and len(result) >= 5:
                # 清理公司名称
                company_name = str(result[1]) if len(result) > 1 and result[1] else ""
                if company_name.startswith("名称："):
                    company_name = company_name[3:]
                
                data_dict = {
                    "文件路径": str(result[0]) if len(result) > 0 else "",
                    "开票公司名称": company_name,
                    "发票号码": str(result[2]) if len(result) > 2 and result[2] else "",
                    "发票日期": str(result[3]) if len(result) > 3 and result[3] else "",
                    "金额（价税合计）": str(result[4]) if len(result) > 4 and result[4] else "",
                    "项目名称": str(result[5]) if len(result) > 5 and result[5] else ""
                }
                data_list.append(data_dict)
        
        if not data_list:
            return None
        
        # 创建Excel文件
        df = pd.DataFrame(data_list)
        excel_path = os.path.join(
            app.config['RESULTS_FOLDER'], 
            f'发票识别结果_{task_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
        df.to_excel(excel_path, index=False)
        return excel_path
        
    except Exception as e:
        print(f"保存Excel文件失败: {e}")
        return None

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    print('客户端已连接')
    emit('status', {'message': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开连接')

if __name__ == '__main__':
    print("🚀 InvoiceVision Web服务器启动中...")
    print(f"📂 上传目录: {app.config['UPLOAD_FOLDER']}")
    print(f"📂 结果目录: {app.config['RESULTS_FOLDER']}")
    print(f"📂 模型目录: {app.config['MODELS_FOLDER']}")
    
    # 生产模式下运行（Docker环境）
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)
