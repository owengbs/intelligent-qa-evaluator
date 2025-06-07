#!/usr/bin/env python3
"""
图片上传相关路由
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from utils.logger import get_logger
import base64
import imghdr

upload_bp = Blueprint('upload', __name__)
logger = get_logger(__name__)

# 允许的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image(file_data):
    """验证是否为有效图片"""
    try:
        # 检测图片格式
        image_format = imghdr.what(None, h=file_data)
        return image_format in ['png', 'jpeg', 'gif', 'webp', 'bmp']
    except:
        return False

def create_upload_folder():
    """创建上传文件夹"""
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'images')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

def generate_unique_filename(original_filename):
    """生成唯一文件名"""
    # 获取文件扩展名
    if '.' in original_filename:
        ext = original_filename.rsplit('.', 1)[1].lower()
    else:
        ext = 'png'  # 默认扩展名
    
    # 生成唯一文件名：时间戳 + UUID + 扩展名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{timestamp}_{unique_id}.{ext}"
    return filename

@upload_bp.route('/api/upload/image', methods=['POST'])
def upload_image():
    """
    上传图片接口
    支持两种方式：
    1. FormData文件上传
    2. Base64数据上传
    """
    try:
        upload_folder = create_upload_folder()
        
        # 方式1: FormData文件上传
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                # 验证文件类型
                if not allowed_file(file.filename):
                    return jsonify({
                        'success': False,
                        'message': '不支持的文件格式，仅支持: png, jpg, jpeg, gif, webp, bmp'
                    }), 400
                
                # 验证文件大小
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    return jsonify({
                        'success': False,
                        'message': f'文件过大，最大支持 {MAX_FILE_SIZE // 1024 // 1024}MB'
                    }), 400
                
                # 读取文件数据并验证图片
                file_data = file.read()
                if not validate_image(file_data):
                    return jsonify({
                        'success': False,
                        'message': '无效的图片文件'
                    }), 400
                
                # 生成安全的文件名
                original_filename = secure_filename(file.filename)
                filename = generate_unique_filename(original_filename)
                file_path = os.path.join(upload_folder, filename)
                
                # 保存文件
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                # 返回结果
                url = f"/api/static/uploads/images/{filename}"
                return jsonify({
                    'success': True,
                    'message': '图片上传成功',
                    'data': {
                        'id': str(uuid.uuid4()),
                        'name': original_filename,
                        'filename': filename,
                        'url': url,
                        'size': file_size,
                        'type': file.content_type or 'image/png',
                        'upload_time': datetime.now().isoformat()
                    }
                })
        
        # 方式2: Base64数据上传
        elif request.json and 'imageData' in request.json:
            image_data = request.json['imageData']
            filename = request.json.get('filename', 'pasted_image.png')
            
            # 处理base64数据
            if image_data.startswith('data:image/'):
                # 提取base64数据
                header, base64_data = image_data.split(',', 1)
                # 从header中提取文件类型
                image_type = header.split(';')[0].split(':')[1].split('/')[1]
                file_data = base64.b64decode(base64_data)
            else:
                return jsonify({
                    'success': False,
                    'message': '无效的base64图片数据'
                }), 400
            
            # 验证文件大小
            if len(file_data) > MAX_FILE_SIZE:
                return jsonify({
                    'success': False,
                    'message': f'文件过大，最大支持 {MAX_FILE_SIZE // 1024 // 1024}MB'
                }), 400
            
            # 验证图片
            if not validate_image(file_data):
                return jsonify({
                    'success': False,
                    'message': '无效的图片数据'
                }), 400
            
            # 生成文件名
            original_filename = secure_filename(filename)
            unique_filename = generate_unique_filename(f"paste.{image_type}")
            file_path = os.path.join(upload_folder, unique_filename)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # 返回结果
            url = f"/api/static/uploads/images/{unique_filename}"
            return jsonify({
                'success': True,
                'message': '图片上传成功',
                'data': {
                    'id': str(uuid.uuid4()),
                    'name': original_filename,
                    'filename': unique_filename,
                    'url': url,
                    'size': len(file_data),
                    'type': f'image/{image_type}',
                    'upload_time': datetime.now().isoformat()
                }
            })
        
        else:
            return jsonify({
                'success': False,
                'message': '未找到图片数据'
            }), 400
            
    except Exception as e:
        logger.error(f"图片上传失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'图片上传失败: {str(e)}'
        }), 500

@upload_bp.route('/api/static/uploads/images/<filename>')
def serve_uploaded_image(filename):
    """提供上传的图片文件"""
    try:
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'images')
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        logger.error(f"图片文件服务失败: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

@upload_bp.route('/api/upload/images/cleanup', methods=['POST'])
def cleanup_temp_images():
    """清理临时图片文件（可选功能）"""
    try:
        # 获取要清理的图片列表
        image_urls = request.json.get('imageUrls', [])
        
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'images')
        deleted_count = 0
        
        for url in image_urls:
            if url.startswith('/api/static/uploads/images/'):
                filename = url.split('/')[-1]
                file_path = os.path.join(upload_folder, filename)
                
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"删除临时图片: {filename}")
                    except OSError as e:
                        logger.warning(f"删除图片失败 {filename}: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'清理完成，删除了 {deleted_count} 个临时图片'
        })
        
    except Exception as e:
        logger.error(f"清理临时图片失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'清理失败: {str(e)}'
        }), 500 