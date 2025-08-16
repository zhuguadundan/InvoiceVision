/**
 * InvoiceVision Web应用程序主要JavaScript文件
 * 包含文件上传、OCR处理、实时进度和结果展示功能
 */

class InvoiceVisionApp {
    constructor() {
        this.socket = null;
        this.uploadedFiles = [];
        this.currentTaskId = null;
        this.results = [];
        this.allResults = []; // 存储所有历史结果
        
        this.init();
    }
    
    init() {
        this.initSocket();
        this.bindEvents();
        this.loadPersistedData(); // 加载持久化数据
        this.setupFileUpload();
    }
    
    // 初始化WebSocket连接
    initSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.updateConnectionStatus(true);
            this.showNotification('WebSocket连接成功', 'success');
        });
        
        this.socket.on('disconnect', () => {
            this.updateConnectionStatus(false);
            this.showNotification('WebSocket连接断开', 'warning');
        });
        
        this.socket.on('progress_update', (data) => {
            this.handleProgressUpdate(data);
        });
    }
    
    // 更新连接状态
    updateConnectionStatus(connected) {
        const indicator = document.getElementById('status-indicator');
        if (connected) {
            indicator.innerHTML = '<i class="fas fa-circle text-success me-1"></i>已连接';
        } else {
            indicator.innerHTML = '<i class="fas fa-circle text-danger me-1"></i>连接断开';
        }
    }
    
    // 加载持久化数据
    loadPersistedData() {
        try {
            const savedResults = localStorage.getItem('invoiceVision_allResults');
            if (savedResults) {
                this.allResults = JSON.parse(savedResults);
                this.results = this.allResults; // 显示所有历史结果
                this.updateResultsTable();
                
                // 启用下载按钮如果有数据
                if (this.allResults.length > 0) {
                    document.getElementById('download-excel').disabled = false;
                    document.getElementById('download-json').disabled = false;
                }
            }
        } catch (error) {
            console.error('加载持久化数据失败:', error);
            this.allResults = [];
        }
    }
    
    // 保存数据到localStorage
    saveDataToPersistence() {
        try {
            localStorage.setItem('invoiceVision_allResults', JSON.stringify(this.allResults));
        } catch (error) {
            console.error('保存数据到本地存储失败:', error);
        }
    }
    
    // 绑定事件处理器
    bindEvents() {
        // 文件上传相关
        document.getElementById('browse-files').addEventListener('click', (e) => {
            e.stopPropagation(); // 阻止事件冒泡到upload-area
            document.getElementById('file-input').click();
        });
        
        document.getElementById('file-input').addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files);
        });
        
        // 拖拽上传
        const uploadArea = document.getElementById('upload-area');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFileSelect(e.dataTransfer.files);
        });
        
        uploadArea.addEventListener('click', () => {
            document.getElementById('file-input').click();
        });
        
        // 处理按钮
        document.getElementById('start-processing').addEventListener('click', () => {
            this.startProcessing();
        });
        
        // 清理按钮
        document.getElementById('clear-files').addEventListener('click', () => {
            this.clearFiles();
        });
        
        document.getElementById('clear-results').addEventListener('click', () => {
            this.clearResults();
        });
        
        // 下载按钮
        document.getElementById('download-excel').addEventListener('click', () => {
            this.downloadResults('excel');
        });
        
        document.getElementById('download-json').addEventListener('click', () => {
            this.downloadResults('json');
        });
    }
    
    // 设置文件上传
    setupFileUpload() {
        // 防止页面默认的拖拽行为
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });
    }
    
    // 处理文件选择
    async handleFileSelect(files) {
        if (!files || files.length === 0) return;
        
        const formData = new FormData();
        const validFiles = [];
        
        // 验证文件
        for (let file of files) {
            if (this.validateFile(file)) {
                formData.append('files', file);
                validFiles.push(file);
            }
        }
        
        if (validFiles.length === 0) {
            this.showNotification('没有有效的文件可上传', 'warning');
            return;
        }
        
        try {
            this.showLoading('上传文件中...');
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.uploadedFiles = this.uploadedFiles.concat(data.files);
                this.updateFileList();
                this.updateProcessButton();
                this.showNotification(data.message, 'success');
            } else {
                this.showNotification('上传失败: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('上传失败:', error);
            this.showNotification('上传失败: ' + error.message, 'error');
        } finally {
            this.hideLoading();
            // 重置文件输入
            document.getElementById('file-input').value = '';
        }
    }
    
    // 验证文件
    validateFile(file) {
        // 检查文件大小 (500MB)
        if (file.size > 500 * 1024 * 1024) {
            this.showNotification(`文件 ${file.name} 过大 (超过500MB)`, 'warning');
            return false;
        }
        
        // 检查文件类型
        const allowedTypes = ['.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'];
        const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        
        if (!allowedTypes.includes(extension)) {
            this.showNotification(`不支持的文件类型: ${file.name}`, 'warning');
            return false;
        }
        
        return true;
    }
    
    // 更新文件列表显示
    updateFileList() {
        const fileList = document.getElementById('file-list');
        const fileCount = document.getElementById('file-count');
        
        fileCount.textContent = this.uploadedFiles.length;
        
        if (this.uploadedFiles.length === 0) {
            fileList.innerHTML = `
                <div class="list-group-item text-center text-muted py-4">
                    <i class="fas fa-folder-open fa-2x mb-2 opacity-50"></i><br>
                    暂无文件
                </div>
            `;
            return;
        }
        
        fileList.innerHTML = '';
        
        this.uploadedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = `list-group-item file-item ${file.file_type}`;
            
            const iconClass = file.file_type === 'pdf' ? 'fas fa-file-pdf text-danger' : 'fas fa-image text-success';
            const fileSize = this.formatFileSize(file.file_size);
            
            fileItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <i class="${iconClass} me-2 file-icon ${file.file_type}"></i>
                        <div>
                            <div class="fw-medium text-truncate" style="max-width: 200px;" title="${file.original_name}">
                                ${file.original_name}
                            </div>
                            <div class="file-size">${fileSize}</div>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-outline-danger file-remove" onclick="app.removeFile(${index})" title="移除文件">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            fileList.appendChild(fileItem);
        });
    }
    
    // 移除文件
    removeFile(index) {
        this.uploadedFiles.splice(index, 1);
        this.updateFileList();
        this.updateProcessButton();
    }
    
    // 更新处理按钮状态
    updateProcessButton() {
        const button = document.getElementById('start-processing');
        button.disabled = this.uploadedFiles.length === 0;
    }
    
    // 开始处理
    async startProcessing() {
        if (this.uploadedFiles.length === 0) {
            this.showNotification('请先上传文件', 'warning');
            return;
        }
        
        const precisionMode = document.getElementById('precision-mode').value;
        
        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    files: this.uploadedFiles,
                    precision_mode: precisionMode
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.currentTaskId = data.task_id;
                this.showProgressCard();
                this.updateProcessingUI(true);
                this.showNotification(data.message, 'success');
            } else {
                this.showNotification('启动处理失败: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('启动处理失败:', error);
            this.showNotification('启动处理失败: ' + error.message, 'error');
        }
    }
    
    // 显示进度卡片
    showProgressCard() {
        const progressCard = document.getElementById('progress-card');
        progressCard.style.display = 'block';
        progressCard.classList.add('animate__animated', 'animate__fadeInDown');
        
        // 重置进度
        this.updateProgress(0, '准备开始...', '');
    }
    
    // 隐藏进度卡片
    hideProgressCard() {
        const progressCard = document.getElementById('progress-card');
        progressCard.style.display = 'none';
    }
    
    // 更新进度
    updateProgress(percent, message, time) {
        const progressBar = document.getElementById('progress-bar');
        const progressMessage = document.getElementById('progress-message');
        const progressTime = document.getElementById('progress-time');
        
        progressBar.style.width = percent + '%';
        progressBar.textContent = Math.round(percent) + '%';
        progressMessage.textContent = message;
        if (time) progressTime.textContent = time;
    }
    
    // 处理进度更新
    handleProgressUpdate(data) {
        // 检查task_id是否匹配（考虑子任务的情况）
        if (!data.task_id || !this.currentTaskId) return;
        if (!data.task_id.startsWith(this.currentTaskId)) return;
        
        const percent = data.progress || 0;
        const message = data.message || '';
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        
        this.updateProgress(percent, message, timestamp);
        
        // 检查是否是主任务完成（而非子任务）
        if (data.data && data.data.completed && data.task_id === this.currentTaskId) {
            this.handleProcessingComplete(data.data);
        }
        // 检查子任务完成的情况
        else if (data.data && data.data.results && data.task_id !== this.currentTaskId) {
            // 子任务完成，可以显示部分结果，但不结束整个处理
            console.log('子任务完成:', data.task_id, '结果数量:', data.data.results.length);
        }
        
        // 检查是否出错
        if (data.data && data.data.error) {
            this.handleProcessingError(data.data.error);
        }
    }
    
    // 处理完成
    handleProcessingComplete(data) {
        // 获取新结果
        const newResults = data.results || [];
        
        // 更新当前结果（用于当前会话显示）
        this.results = this.results.concat(newResults);
        
        // 更新所有历史结果（用于持久化）
        this.allResults = this.allResults.concat(newResults);
        
        // 保存到本地存储
        this.saveDataToPersistence();
        
        this.updateResultsTable();
        this.updateProcessingUI(false);
        this.hideProgressCard();
        this.showNotification(`处理完成！新增 ${newResults.length} 条记录`, 'success');
        
        // 启用下载按钮
        document.getElementById('download-excel').disabled = false;
        document.getElementById('download-json').disabled = false;
        
        console.log('处理完成，总历史结果数:', this.allResults.length);
    }
    
    // 处理错误
    handleProcessingError(error) {
        this.updateProcessingUI(false);
        this.showNotification('处理出错: ' + error, 'error');
    }
    
    // 更新处理界面状态
    updateProcessingUI(processing) {
        const startButton = document.getElementById('start-processing');
        const precisionSelect = document.getElementById('precision-mode');
        const browseButton = document.getElementById('browse-files');
        const clearButton = document.getElementById('clear-files');
        
        if (processing) {
            startButton.disabled = true;
            startButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>处理中...';
            precisionSelect.disabled = true;
            browseButton.disabled = true;
            clearButton.disabled = true;
        } else {
            startButton.disabled = this.uploadedFiles.length === 0;
            startButton.innerHTML = '<i class="fas fa-play me-2"></i>开始处理';
            precisionSelect.disabled = false;
            browseButton.disabled = false;
            clearButton.disabled = false;
        }
    }
    
    // 更新结果表格
    updateResultsTable() {
        const tbody = document.getElementById('results-tbody');
        const resultsCount = document.getElementById('results-count');
        
        // 使用所有历史结果
        const displayResults = this.allResults;
        resultsCount.textContent = displayResults.length;
        
        if (displayResults.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-muted py-5">
                        <i class="fas fa-search fa-3x mb-3 opacity-50"></i><br>
                        <h5>暂无识别结果</h5>
                        <p>上传发票文件并开始处理以查看识别结果</p>
                    </td>
                </tr>
            `;
            this.updateStatistics(0, 0, 0);
            return;
        }
        
        tbody.innerHTML = '';
        
        let recognizedCount = 0;
        
        displayResults.forEach((result, index) => {
            const row = document.createElement('tr');
            row.className = 'fade-in';
            
            // 处理结果数据
            let companyName = '', invoiceNumber = '', invoiceDate = '', projectName = '', amount = '', fileName = '';
            
            if (Array.isArray(result) && result.length >= 5) {
                fileName = result[0] ? this.extractFileName(result[0]) : '';
                companyName = result[1] ? result[1].replace(/^名称：/, '') : '';
                invoiceNumber = result[2] || '';
                invoiceDate = result[3] || '';
                amount = result[4] || '';
                projectName = result[5] || '';
                
                if (companyName || invoiceNumber) {
                    recognizedCount++;
                }
            }
            
            row.innerHTML = `
                <td class="text-truncate" style="max-width: 200px;" title="${companyName}">${companyName}</td>
                <td class="text-center">${invoiceNumber}</td>
                <td class="text-center">${invoiceDate}</td>
                <td class="text-truncate" style="max-width: 250px;" title="${projectName}">${projectName}</td>
                <td class="text-end text-success fw-bold">${amount}</td>
                <td class="text-truncate text-muted small" style="max-width: 150px;" title="${fileName}">${fileName}</td>
            `;
            
            tbody.appendChild(row);
        });
        
        this.updateStatistics(this.uploadedFiles.length, displayResults.length, recognizedCount);
    }
    
    // 更新统计信息
    updateStatistics(totalFiles, processedFiles, recognizedInvoices) {
        document.getElementById('total-files').textContent = totalFiles;
        document.getElementById('processed-files').textContent = processedFiles;
        document.getElementById('recognized-invoices').textContent = recognizedInvoices;
        
        const successRate = processedFiles > 0 ? Math.round((recognizedInvoices / processedFiles) * 100) : 0;
        document.getElementById('success-rate').textContent = successRate + '%';
    }
    
    // 提取文件名
    extractFileName(filePath) {
        if (!filePath) return '';
        const parts = filePath.split(/[/\\]/);
        return parts[parts.length - 1] || '';
    }
    
    // 清理文件
    clearFiles() {
        this.uploadedFiles = [];
        this.updateFileList();
        this.updateProcessButton();
        this.showNotification('已清空文件列表', 'info');
    }
    
    // 清理结果
    clearResults() {
        this.results = [];
        this.allResults = []; // 也清空历史结果
        this.currentTaskId = null;
        
        // 清除本地存储
        localStorage.removeItem('invoiceVision_allResults');
        
        this.updateResultsTable();
        this.hideProgressCard();
        document.getElementById('download-excel').disabled = true;
        document.getElementById('download-json').disabled = true;
        this.showNotification('已清空所有结果', 'info');
    }
    
    // 下载结果
    async downloadResults(format) {
        if (this.allResults.length === 0) {
            this.showNotification('没有可下载的结果', 'warning');
            return;
        }
        
        try {
            const response = await fetch(`/api/results/all/${format}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    results: this.allResults
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `发票识别历史结果_${new Date().toISOString().slice(0,10)}.${format === 'excel' ? 'xlsx' : 'json'}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showNotification(`${format.toUpperCase()}文件下载成功`, 'success');
            } else {
                const data = await response.json();
                this.showNotification('下载失败: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('下载失败:', error);
            this.showNotification('下载失败: ' + error.message, 'error');
        }
    }
    
    // 显示通知
    showNotification(message, type = 'info') {
        const toast = document.getElementById('notification-toast');
        const toastMessage = document.getElementById('toast-message');
        
        // 设置消息内容
        toastMessage.textContent = message;
        
        // 设置样式
        toast.className = 'toast';
        switch(type) {
            case 'success':
                toast.classList.add('bg-success', 'text-white');
                break;
            case 'error':
                toast.classList.add('bg-danger', 'text-white');
                break;
            case 'warning':
                toast.classList.add('bg-warning', 'text-dark');
                break;
            default:
                toast.classList.add('bg-info', 'text-white');
        }
        
        // 显示Toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
    
    // 显示加载状态
    showLoading(message = '加载中...') {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.id = 'loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="text-center">
                <div class="loading-spinner mb-3"></div>
                <div class="fw-bold">${message}</div>
            </div>
        `;
        document.body.appendChild(loadingOverlay);
    }
    
    // 隐藏加载状态
    hideLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }
    
    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// 初始化应用程序
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new InvoiceVisionApp();
});