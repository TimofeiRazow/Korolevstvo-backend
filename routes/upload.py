# routes/upload.py
import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from PIL import Image
import logging

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Проверка расширения файла"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_thumbnail(image_path, thumbnail_path, size=(300, 300)):
    """Создание миниатюры изображения"""
    try:
        with Image.open(image_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Создаем миниатюру с сохранением пропорций
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            
        return True
    except Exception as e:
        logger.error(f"Ошибка создания миниатюры: {str(e)}")
        return False

def optimize_image(image_path, max_width=1920):
    """Оптимизация изображения"""
    try:
        with Image.open(image_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Уменьшаем размер если нужно
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Сохраняем оптимизированное изображение
            img.save(image_path, 'JPEG', quality=85, optimize=True)
            
        return True
    except Exception as e:
        logger.error(f"Ошибка оптимизации изображения: {str(e)}")
        return False

@upload_bp.route('/image', methods=['POST'])
def upload_image():
    """Загрузка одного изображения"""
    try:
        # Проверяем наличие файла
        if 'image' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        # Проверяем размер файла
        if len(file.read()) > MAX_FILE_SIZE:
            return jsonify({'error': 'Файл превышает максимальный размер 10MB'}), 400
        
        # Сбрасываем позицию в файле
        file.seek(0)
        
        # Проверяем расширение
        if not allowed_file(file.filename):
            return jsonify({'error': 'Недопустимый тип файла'}), 400
        
        # Создаем безопасное имя файла
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Создаем директории если не существуют
        images_dir = os.path.join(current_app.static_folder, 'images')
        thumbnails_dir = os.path.join(images_dir, 'thumbnails')
        
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # Сохраняем оригинальный файл
        file_path = os.path.join(images_dir, unique_filename)
        file.save(file_path)
        
        # Оптимизируем изображение
        optimize_image(file_path)
        
        # Создаем миниатюру
        thumbnail_filename = f"thumb_{unique_filename}"
        thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
        create_thumbnail(file_path, thumbnail_path)
        
        # Формируем URL для доступа к изображению
        base_url = request.url_root.rstrip('/')
        image_url = f"{base_url}/static/images/{unique_filename}"
        thumbnail_url = f"{base_url}/static/images/thumbnails/{thumbnail_filename}"
        
        logger.info(f"Изображение загружено: {unique_filename}")
        
        return jsonify({
            'message': 'Изображение загружено успешно',
            'url': image_url,
            'thumbnail_url': thumbnail_url,
            'filename': unique_filename,
            'original_name': filename
        }), 201
        
    except Exception as e:
        logger.error(f"Ошибка загрузки изображения: {str(e)}")
        return jsonify({'error': 'Ошибка при загрузке изображения'}), 500

@upload_bp.route('/images', methods=['POST'])
def upload_multiple_images():
    """Загрузка нескольких изображений"""
    try:
        uploaded_files = request.files.getlist('images')
        
        if not uploaded_files:
            return jsonify({'error': 'Файлы не найдены'}), 400
        
        results = []
        errors = []
        
        # Создаем директории если не существуют
        images_dir = os.path.join(current_app.static_folder, 'images')
        thumbnails_dir = os.path.join(images_dir, 'thumbnails')
        
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        for file in uploaded_files:
            try:
                # Проверки файла
                if file.filename == '':
                    errors.append('Пустое имя файла')
                    continue
                
                if len(file.read()) > MAX_FILE_SIZE:
                    errors.append(f'{file.filename}: Файл превышает максимальный размер')
                    continue
                
                file.seek(0)
                
                if not allowed_file(file.filename):
                    errors.append(f'{file.filename}: Недопустимый тип файла')
                    continue
                
                # Сохраняем файл
                filename = secure_filename(file.filename)
                file_extension = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
                
                file_path = os.path.join(images_dir, unique_filename)
                file.save(file_path)
                
                # Оптимизируем
                optimize_image(file_path)
                
                # Создаем миниатюру
                thumbnail_filename = f"thumb_{unique_filename}"
                thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
                create_thumbnail(file_path, thumbnail_path)
                
                # Формируем URLs
                base_url = request.url_root.rstrip('/')
                image_url = f"{base_url}/static/images/{unique_filename}"
                thumbnail_url = f"{base_url}/static/images/thumbnails/{thumbnail_filename}"
                
                results.append({
                    'url': image_url,
                    'thumbnail_url': thumbnail_url,
                    'filename': unique_filename,
                    'original_name': filename
                })
                
            except Exception as e:
                errors.append(f'{file.filename}: {str(e)}')
                continue
        
        logger.info(f"Загружено {len(results)} изображений")
        
        return jsonify({
            'message': f'Загружено {len(results)} изображений',
            'images': results,
            'errors': errors
        }), 201
        
    except Exception as e:
        logger.error(f"Ошибка загрузки изображений: {str(e)}")
        return jsonify({'error': 'Ошибка при загрузке изображений'}), 500

@upload_bp.route('/delete/<filename>', methods=['DELETE'])
def delete_image(filename):
    """Удаление изображения"""
    try:
        # Проверяем безопасность имени файла
        safe_filename = secure_filename(filename)
        
        # Пути к файлам
        images_dir = os.path.join(current_app.static_folder, 'images')
        image_path = os.path.join(images_dir, safe_filename)
        thumbnail_path = os.path.join(images_dir, 'thumbnails', f"thumb_{safe_filename}")
        
        deleted_files = []
        
        # Удаляем основное изображение
        if os.path.exists(image_path):
            os.remove(image_path)
            deleted_files.append('image')
        
        # Удаляем миниатюру
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
            deleted_files.append('thumbnail')
        
        if not deleted_files:
            return jsonify({'error': 'Файл не найден'}), 404
        
        logger.info(f"Удалено изображение: {safe_filename}")
        
        return jsonify({
            'message': 'Изображение удалено успешно',
            'deleted_files': deleted_files
        })
        
    except Exception as e:
        logger.error(f"Ошибка удаления изображения {filename}: {str(e)}")
        return jsonify({'error': 'Ошибка при удалении изображения'}), 500