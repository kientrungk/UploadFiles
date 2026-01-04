from flask import Flask, render_template_string, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['BASE_UPLOAD_FOLDER'] = 'clinic_uploads'

os.makedirs(app.config['BASE_UPLOAD_FOLDER'], exist_ok=True)

METADATA_FILE = os.path.join(app.config['BASE_UPLOAD_FOLDER'], 'metadata.json')

def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_metadata(data):
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def allowed_file(filename):
    allowed = ['xlsx', 'xls', 'csv', 'doc', 'docx', 'pdf', 'jpg', 'jpeg', 'png', 'zip', 'rar']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    units = ['B', 'KB', 'MB', 'GB']
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {units[i]}"

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <title>Quản Lý File Siêu Âm</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f0f0;
            height: 100vh;
            overflow: hidden;
        }
        
        .toolbar {
            background: #fff;
            padding: 10px 20px;
            border-bottom: 1px solid #ccc;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .toolbar h1 {
            font-size: 16px;
            color: #333;
            margin-right: 20px;
        }
            #toast {
        visibility: hidden;
        min-width: 250px;
        margin-left: -125px;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 4px;
        padding: 16px;
        position: fixed;
        z-index: 9999;
        left: 50%;
        bottom: 30px;
        font-size: 16px;
        opacity: 0;
        transition: opacity 0.5s, bottom 0.5s;
    }

        #toast.show {
            visibility: visible;
            opacity: 1;
            bottom: 50px;
        }

        
        .btn {
            padding: 8px 16px;
            border: 1px solid #ccc;
            background: #f5f5f5;
            border-radius: 3px;
            cursor: pointer;
            font-size: 13px;
            color: #333;
            transition: all 0.2s;
        }
        
        .btn:hover {
            background: #e0e0e0;
        }
        
        .btn-primary {
            background: #0078d4;
            color: white;
            border-color: #0078d4;
        }
        
        .btn-primary:hover {
            background: #106ebe;
        }
        
        .main-container {
            display: flex;
            height: calc(100vh - 51px);
        }
        
        .sidebar {
            width: 280px;
            background: #fff;
            border-right: 1px solid #ccc;
            overflow-y: auto;
        }
        
        .folder-item {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .folder-item:hover {
            background: #f5f5f5;
        }
        
        .folder-item.selected {
            background: #e5f3ff;
            border-left: 3px solid #0078d4;
        }
        
        .folder-item.expanded {
            background: #fafafa;
        }
        
        .folder-name {
            font-weight: 600;
            font-size: 14px;
            color: #333;
            margin-bottom: 3px;
        }
        
        .folder-info {
            font-size: 12px;
            color: #666;
        }
        
        .folder-details {
            display: none;
            padding: 10px 15px;
            background: #f9f9f9;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
        }
        
        .folder-details.show {
            display: block;
        }
        
        .folder-detail-item {
            padding: 5px 0;
            color: #555;
        }
        
        .folder-actions {
            margin-top: 8px;
            display: flex;
            gap: 5px;
        }
        
        .folder-actions .btn {
            padding: 4px 10px;
            font-size: 11px;
        }
        
        .content {
            flex: 1;
            background: #fff;
            overflow-y: auto;
            padding: 20px;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        
        .empty-state h2 {
            font-size: 18px;
            margin-bottom: 10px;
        }
        
        .file-list {
            margin-top: 20px;
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border: 1px solid #e0e0e0;
            border-radius: 3px;
            margin-bottom: 8px;
            background: #fafafa;
        }
        
        .file-item:hover {
            background: #f5f5f5;
        }
        
        .file-info {
            flex: 1;
        }
        
        .file-name {
            font-weight: 500;
            font-size: 14px;
            color: #333;
        }
        
        .file-meta {
            font-size: 11px;
            color: #666;
            margin-top: 3px;
        }
        
        .file-actions {
            display: flex;
            gap: 5px;
        }
        
        .file-actions .btn {
            padding: 5px 12px;
            font-size: 12px;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal.show {
            display: flex;
        }
        
        .modal-content {
            background: white;
            border-radius: 8px;
            width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .modal-header {
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
            font-size: 16px;
            font-weight: 600;
        }
        
        .modal-body {
            padding: 20px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            font-size: 13px;
            color: #555;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 8px 10px;
            border: 1px solid #ccc;
            border-radius: 3px;
            font-size: 13px;
            font-family: inherit;
        }
        
        .form-group input:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #0078d4;
        }
        
        .file-upload-box {
            border: 2px dashed #ccc;
            border-radius: 4px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .file-upload-box:hover {
            border-color: #0078d4;
            background: #f9f9f9;
        }
        
        .file-upload-box.dragover {
            border-color: #0078d4;
            background: #e5f3ff;
        }
        
        .selected-files {
            margin-top: 10px;
            padding: 10px;
            background: #f9f9f9;
            border-radius: 3px;
            display: none;
        }
        
        .selected-files.show {
            display: block;
        }
        
        .selected-file {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 5px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 3px;
            margin-bottom: 5px;
            font-size: 12px;
        }
        
        .remove-file {
            color: #d13438;
            cursor: pointer;
            font-weight: bold;
        }
        
        .modal-footer {
            padding: 15px 20px;
            border-top: 1px solid #e0e0e0;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }
        
        .content-header {
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .content-header h2 {
            font-size: 18px;
            color: #333;
            margin-bottom: 5px;
        }
        
        .content-header p {
            font-size: 13px;
            color: #666;
        }
        
        .no-folder {
            color: #999;
            text-align: center;
            padding: 40px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="toolbar">
        <h1>🗂️ Quản Lý File - Đại ca 99 Bắc Ninh</h1>

        <button class="btn btn-primary" onclick="openCreateModal()">+ Tạo Đoàn Khám</button>
    </div>
    
    <div class="main-container">
        <div class="sidebar" id="sidebar">
            <div class="no-folder">Chưa có đoàn khám nào</div>
        </div>
        
        <div class="content">
            <div class="empty-state" id="emptyState">
                <h2>👈 Chọn đoàn khám để xem chi tiết</h2>
                <p>Hoặc tạo đoàn khám mới để bắt đầu</p>
            </div>
            
            <div id="folderContent" style="display: none;">
                <div class="content-header">
                    <h2 id="contentTitle">-</h2>
                    <p id="contentInfo">-</p>
                </div>
                
                <div>
                    <button class="btn btn-primary" onclick="openUploadModal()">+ Upload File</button>
                </div>
                
                <div class="file-list" id="fileList"></div>
            </div>
        </div>
    </div>
    
    <!-- Modal Tạo/Sửa -->
    <div class="modal" id="createModal">
        <div class="modal-content">
            <div class="modal-header" id="modalTitle">Tạo Đoàn Khám Mới</div>
            <div class="modal-body">
                <form id="folderForm">
                    <input type="hidden" id="editFolderName">
                    
                    <div class="form-group">
                        <label>Tên Công Ty *</label>
                        <input type="text" id="companyName" required placeholder="Nhập tên công ty">
                    </div>
                    
                    <div class="form-group">
                        <label>Ngày Khám *</label>
                        <input type="date" id="examDate" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Ghi Chú</label>
                        <textarea id="notes" rows="3" placeholder="Ghi chú..."></textarea>
                    </div>
                    
                    <div class="form-group" id="uploadGroup">
                        <label>Chọn File (Tùy chọn)</label>
                        <div class="file-upload-box" id="dropArea">
                            <div style="font-size: 36px; margin-bottom: 10px;">📁</div>
                            <div>Kéo thả file hoặc click để chọn</div>
                            <div style="font-size: 11px; color: #999; margin-top: 5px;">Excel, Word, PDF, Hình ảnh</div>
                        </div>
                        <input type="file" id="fileInput" multiple style="display: none;"
                               accept=".xlsx,.xls,.csv,.doc,.docx,.pdf,.jpg,.jpeg,.png,.zip,.rar">
                        
                        <div class="selected-files" id="selectedFiles">
                            <div id="filesList"></div>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn" onclick="closeModal()">Hủy</button>
                <button class="btn btn-primary" onclick="saveFolder()">Lưu</button>
            </div>
        </div>
    </div>
    
    <!-- Modal Upload File -->
    <div class="modal" id="uploadModal">
        <div class="modal-content">
            <div class="modal-header">Upload File</div>
            <div class="modal-body">
                <div class="file-upload-box" id="uploadDropArea">
                    <div style="font-size: 36px; margin-bottom: 10px;">📁</div>
                    <div>Kéo thả file hoặc click để chọn</div>
                    <div style="font-size: 11px; color: #999; margin-top: 5px;">Excel, Word, PDF, Hình ảnh</div>
                </div>
                <input type="file" id="uploadFileInput" multiple style="display: none;"
                       accept=".xlsx,.xls,.csv,.doc,.docx,.pdf,.jpg,.jpeg,.png,.zip,.rar">
                
                <div class="selected-files" id="uploadSelectedFiles">
                    <div id="uploadFilesList"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn" onclick="closeUploadModal()">Hủy</button>
                <button class="btn btn-primary" onclick="uploadFiles()">Upload</button>
            </div>
        </div>
    </div>
    
    <script>
/* ================== BIẾN TOÀN CỤC ================== */
let selectedFiles = [];
let uploadFileList = []; // 🔥 đổi tên (KHÔNG trùng hàm)
let currentFolder = null;
let isEditMode = false;

/* ================== MODAL CREATE ================== */
function openCreateModal() {
    isEditMode = false;
    document.getElementById('modalTitle').textContent = 'Tạo Đoàn Khám Mới';
    document.getElementById('editFolderName').value = '';
    document.getElementById('companyName').value = '';
    document.getElementById('examDate').valueAsDate = new Date();
    document.getElementById('notes').value = '';
    document.getElementById('uploadGroup').style.display = 'block';
    selectedFiles = [];
    displaySelectedFiles();
    document.getElementById('createModal').classList.add('show');
}

function closeModal() {
    document.getElementById('createModal').classList.remove('show');
    selectedFiles = [];
}

/* ================== MODAL UPLOAD ================== */
function openUploadModal() {
    if (!currentFolder) {
         showToast('Vui lòng chọn đoàn khám trước');
        return;
    }
    uploadFileList = [];
    displayUploadFiles();
    document.getElementById('uploadModal').classList.add('show');
}

function closeUploadModal() {
    document.getElementById('uploadModal').classList.remove('show');
}

/* ================== DRAG & DROP ================== */
window.onload = function () {
    loadFolders();
    document.getElementById('examDate').valueAsDate = new Date();
    setupDragDrop();
};

function setupDragDrop() {
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');

    dropArea.onclick = () => fileInput.click();

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(e =>
        dropArea.addEventListener(e, ev => {
            ev.preventDefault();
            ev.stopPropagation();
        })
    );

    dropArea.addEventListener('drop', e => {
        selectedFiles = Array.from(e.dataTransfer.files);
        displaySelectedFiles();
    });

    fileInput.addEventListener('change', e => {
        selectedFiles = Array.from(e.target.files);
        displaySelectedFiles();
    });

    /* Upload modal */
    const uploadDrop = document.getElementById('uploadDropArea');
    const uploadInput = document.getElementById('uploadFileInput');

    uploadDrop.onclick = () => uploadInput.click();

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(e =>
        uploadDrop.addEventListener(e, ev => {
            ev.preventDefault();
            ev.stopPropagation();
        })
    );

    uploadDrop.addEventListener('drop', e => {
        uploadFileList = Array.from(e.dataTransfer.files);
        displayUploadFiles();
    });

    uploadInput.addEventListener('change', e => {
        uploadFileList = Array.from(e.target.files);
        displayUploadFiles();
    });
}

/* ================== FILE DISPLAY ================== */
function displaySelectedFiles() {
    const box = document.getElementById('selectedFiles');
    const list = document.getElementById('filesList');

    if (!selectedFiles.length) {
        box.classList.remove('show');
        return;
    }

    box.classList.add('show');
    list.innerHTML = selectedFiles.map((f, i) => `
        <div class="selected-file">
            <span>${f.name} (${formatSize(f.size)})</span>
            <span class="remove-file" onclick="removeFile(${i})">×</span>
        </div>
    `).join('');
}

function displayUploadFiles() {
    const box = document.getElementById('uploadSelectedFiles');
    const list = document.getElementById('uploadFilesList');

    if (!uploadFileList.length) {
        box.classList.remove('show');
        return;
    }

    box.classList.add('show');
    list.innerHTML = uploadFileList.map((f, i) => `
        <div class="selected-file">
            <span>${f.name} (${formatSize(f.size)})</span>
            <span class="remove-file" onclick="removeUploadFile(${i})">×</span>
        </div>
    `).join('');
}

function removeFile(i) {
    selectedFiles.splice(i, 1);
    displaySelectedFiles();
}

function removeUploadFile(i) {
    uploadFileList.splice(i, 1);
    displayUploadFiles();
}

/* ================== FORMAT ================== */
function formatSize(bytes) {
    if (!bytes) return '0 B';
    const k = 1024, sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
}

/* ================== SAVE FOLDER ================== */
async function saveFolder() {
    try {
        const companyName = document.getElementById('companyName').value.trim();
        const examDate = document.getElementById('examDate').value;
        const notes = document.getElementById('notes').value.trim();

        if (!companyName || !examDate) {
            showToast('Vui lòng nhập đầy đủ thông tin');
            return;
        }

        if (isEditMode) {
            const folderName = document.getElementById('editFolderName').value;

            const response = await fetch('/update_folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    folder_name: folderName,
                    company_name: companyName,
                    exam_date: examDate,
                    notes: notes
                })
            });

            const result = await response.json();
            if (result.success) {
                 showToast('Cập nhật thành công!');
                closeModal();
                loadFolders();
                if (currentFolder === folderName) {
                    selectFolder(folderName);
                }
            } else {
                showToast(result.message);
            }

        } else {
            const formData = new FormData();
            formData.append('company_name', companyName);
            formData.append('exam_date', examDate);
            formData.append('notes', notes);

            selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            const response = await fetch('/create_folder', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (result.success) {
                showToast('Tạo đoàn khám thành công!');
                closeModal();
                loadFolders();
            } else {
                showToast(result.message);
            }
        }
    } catch (err) {
        console.error(err);
        showToast('Có lỗi: ' + error.message);
    }
}


/* ================== UPLOAD FILE ================== */
async function uploadFiles() {
    if (!uploadFileList.length) {
        showToast('Vui lòng chọn file');
        return;
    }

    const fd = new FormData();
    fd.append('folder_name', currentFolder);
    uploadFileList.forEach(f => fd.append('files', f));

    const res = await fetch('/upload', {method: 'POST', body: fd});
    const r = await res.json();

    if (r.success) {
        closeUploadModal();
        loadFiles(currentFolder);
        loadFolders();
    } else  showToast(r.message);
}
async function loadFolders() {
    try {
        const res = await fetch('/get_folders');
        const data = await res.json();

        const sidebar = document.getElementById('sidebar');

        if (!data.folders || data.folders.length === 0) {
            sidebar.innerHTML = '<div class="no-folder">Chưa có đoàn khám nào</div>';
            return;
        }

        sidebar.innerHTML = data.folders.map(f => `
    <div class="folder-item" id="folder_${f.name}">
        <div onclick="selectFolder('${f.name}')">
            <div class="folder-name">${f.display_name}</div>
            <div class="folder-info">${f.exam_date} • ${f.file_count} file</div>
        </div>
        <div style="margin-top:6px;">
            <button class="btn"
                style="font-size:11px;color:#d13438"
                onclick="event.stopPropagation(); deleteFolder('${f.name}')">
                ❌ Xóa
            </button>
        </div>
    </div>
`).join('');

    } catch (e) {
        console.error(e);
        showToast('Không tải được danh sách đoàn khám');
    }
}
function selectFolder(folderName) {
    const item = document.getElementById('folder_' + folderName);

    if (currentFolder === folderName) {
        // Nếu click vào folder đang chọn -> bỏ chọn
        currentFolder = null;
        item.classList.remove('selected');
        document.getElementById('folderContent').style.display = 'none';
        document.getElementById('emptyState').style.display = 'block';
        return;
    }

    // Xóa class selected của tất cả folder
    document.querySelectorAll('.folder-item').forEach(el => {
        el.classList.remove('selected');
    });

    currentFolder = folderName;
    item.classList.add('selected');

    loadFolderContent(folderName);
}


async function loadFolderContent(folderName) {
    const res = await fetch(`/get_folder_info/${folderName}`);
    const data = await res.json();

    if (!data.success) {
         showToast('Không tải được thông tin đoàn khám');
        return;
    }

    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('folderContent').style.display = 'block';

    document.getElementById('contentTitle').textContent = data.info.company_name;
    document.getElementById('contentInfo').textContent =
        `Ngày khám: ${data.info.exam_date} • ${data.info.notes || 'Không có ghi chú'}`;

    loadFiles(folderName);
}

async function loadFiles(folderName) {
    const res = await fetch(`/get_files/${folderName}`);
    const data = await res.json();

    const container = document.getElementById('fileList');

    if (!data.files || data.files.length === 0) {
        container.innerHTML = '<div style="padding:20px;color:#999">Chưa có file nào</div>';
        return;
    }

    container.innerHTML = data.files.map(f => `
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">${f.name}</div>
                <div class="file-meta">${f.size} • ${f.upload_time}</div>
            </div>
            <div class="file-actions">
                <button class="btn" onclick="downloadFile('${folderName}', '${f.name}')">Tải</button>
                <button class="btn" onclick="deleteFile('${folderName}', '${f.name}')">Xóa</button>
            </div>
        </div>
    `).join('');
}
function downloadFile(folderName, filename) {
    window.location.href = `/download/${folderName}/${filename}`;
}
async function deleteFile(folderName, filename) {
    if (!confirm(`Xóa file "${filename}"?`)) return;

    try {
        const res = await fetch(`/delete/${folderName}/${filename}`, {
            method: 'DELETE'
        });
        const result = await res.json();

        if (result.success) {
            showToast('Xóa thành công!');
            loadFiles(folderName);
            loadFolders();
        } else {
             showToast(result.message || 'Xóa thất bại');
        }
    } catch (err) {
        console.error(err);
         showToast('Có lỗi khi xóa file');
    }
}

function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'show';
    setTimeout(() => {
        toast.className = toast.className.replace('show', '');
    }, duration);
}

/* ================== DELETE FOLDER ================== */
async function deleteFolder(folderName) {
    if (!confirm('Xóa toàn bộ đoàn khám và tất cả file bên trong?')) return;

    try {
        const res = await fetch(`/delete_folder/${folderName}`, {
            method: 'DELETE'
        });
        const result = await res.json();

        if (result.success) {
            showToast('Đã xóa đoàn khám');

            if (currentFolder === folderName) {
                currentFolder = null;
                document.getElementById('folderContent').style.display = 'none';
                document.getElementById('emptyState').style.display = 'block';
            }

            loadFolders();
        } else {
            showToast(result.message || 'Xóa thất bại');
        }
    } catch (e) {
        console.error(e);
        showToast('Lỗi khi xóa đoàn khám');
    }
}
</script>

</script>
<div id="toast"></div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/create_folder', methods=['POST'])
def create_folder():
    try:
        company_name = request.form.get('company_name', '').strip()
        exam_date = request.form.get('exam_date', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not company_name or not exam_date:
            return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin'})
        
        folder_name = f"{company_name}_{exam_date}"
        folder_name = secure_filename(folder_name)
        folder_path = os.path.join(app.config['BASE_UPLOAD_FOLDER'], folder_name)
        
        if os.path.exists(folder_path):
            return jsonify({'success': False, 'message': 'Đoàn khám này đã tồn tại'})
        
        os.makedirs(folder_path)
        
        metadata = load_metadata()
        metadata[folder_name] = {
            'company_name': company_name,
            'exam_date': exam_date,
            'notes': notes,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'files': []
        }
        
        # Upload files if any
        files = request.files.getlist('files')
        if files and files[0].filename != '':
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(folder_path, filename)
                    file.save(file_path)
                    
                    file_size = os.path.getsize(file_path)
                    file_info = {
                        'name': filename,
                        'size': file_size,
                        'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'description': ''
                    }
                    metadata[folder_name]['files'].append(file_info)
        
        save_metadata(metadata)
        
        return jsonify({'success': True, 'folder_name': folder_name})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_folders')
def get_folders():
    try:
        metadata = load_metadata()
        folders = []
        
        for folder_name, info in metadata.items():
            folder_path = os.path.join(app.config['BASE_UPLOAD_FOLDER'], folder_name)
            if os.path.exists(folder_path):
                files = info.get('files', [])
                file_count = len(files)
                total_size = sum(f.get('size', 0) for f in files)
                
                folders.append({
                    'name': folder_name,
                    'display_name': info.get('company_name', folder_name),
                    'exam_date': info.get('exam_date', ''),
                    'notes': info.get('notes', ''),
                    'file_count': file_count,
                    'total_size': format_size(total_size)
                })
        
        folders.sort(key=lambda x: x.get('exam_date', ''), reverse=True)
        return jsonify({'success': True, 'folders': folders})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'folders': []})

@app.route('/get_folder_info/<folder_name>')
def get_folder_info(folder_name):
    try:
        metadata = load_metadata()
        info = metadata.get(folder_name, {})
        return jsonify({'success': True, 'info': info})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/update_folder', methods=['POST'])
def update_folder():
    try:
        data = request.json
        folder_name = data.get('folder_name')
        
        metadata = load_metadata()
        
        if folder_name not in metadata:
            return jsonify({'success': False, 'message': 'Đoàn khám không tồn tại'})
        
        metadata[folder_name]['company_name'] = data.get('company_name', '')
        metadata[folder_name]['exam_date'] = data.get('exam_date', '')
        metadata[folder_name]['notes'] = data.get('notes', '')
        
        save_metadata(metadata)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_folder/<folder_name>', methods=['DELETE'])
def delete_folder(folder_name):
    try:
        folder_path = os.path.join(app.config['BASE_UPLOAD_FOLDER'], folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'message': 'Đoàn khám không tồn tại'})
        
        import shutil
        shutil.rmtree(folder_path)
        
        metadata = load_metadata()
        if folder_name in metadata:
            del metadata[folder_name]
            save_metadata(metadata)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_files/<folder_name>')
def get_files(folder_name):
    try:
        metadata = load_metadata()
        folder_info = metadata.get(folder_name, {})
        files = folder_info.get('files', [])
        
        file_list = []
        for f in files:
            file_list.append({
                'name': f.get('name', ''),
                'size': format_size(f.get('size', 0)),
                'upload_time': f.get('upload_time', ''),
                'description': f.get('description', '')
            })
        
        return jsonify({
            'success': True,
            'files': file_list
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'files': []})

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        folder_name = request.form.get('folder_name')
        
        if not folder_name:
            return jsonify({'success': False, 'message': 'Chưa chọn đoàn khám'})
        
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'message': 'Chưa chọn file'})
        
        folder_path = os.path.join(app.config['BASE_UPLOAD_FOLDER'], folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'message': 'Đoàn khám không tồn tại'})
        
        metadata = load_metadata()
        folder_info = metadata.get(folder_name, {})
        
        uploaded_count = 0
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                base_name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(os.path.join(folder_path, filename)):
                    filename = f"{base_name}_{counter}{ext}"
                    counter += 1
                
                file_path = os.path.join(folder_path, filename)
                file.save(file_path)
                
                file_size = os.path.getsize(file_path)
                file_info = {
                    'name': filename,
                    'size': file_size,
                    'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'description': ''
                }
                
                if 'files' not in folder_info:
                    folder_info['files'] = []
                
                folder_info['files'].append(file_info)
                uploaded_count += 1
        
        metadata[folder_name] = folder_info
        save_metadata(metadata)
        
        return jsonify({
            'success': True,
            'message': f'Upload thành công {uploaded_count} file',
            'uploaded': uploaded_count
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/download/<folder_name>/<filename>')
def download_file(folder_name, filename):
    try:
        file_path = os.path.join(app.config['BASE_UPLOAD_FOLDER'], folder_name, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File không tồn tại'})
        
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete/<folder_name>/<filename>', methods=['DELETE'])
def delete_file(folder_name, filename):
    try:
        file_path = os.path.join(app.config['BASE_UPLOAD_FOLDER'], folder_name, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File không tồn tại'})
        
        os.remove(file_path)
        
        metadata = load_metadata()
        folder_info = metadata.get(folder_name, {})
        
        if 'files' in folder_info:
            folder_info['files'] = [f for f in folder_info['files'] if f.get('name') != filename]
            metadata[folder_name] = folder_info
            save_metadata(metadata)
        
        return jsonify({'success': True, 'message': 'Xóa file thành công'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)