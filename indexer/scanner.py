#!/usr/bin/env python3
"""
Media Scanner - индексатор медиа-файлов для VPS Media Server
Сканирует каталоги с медиа и создает JSON индекс
"""

import os
import sys
import json
import hashlib
import magic
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Настройки из переменных окружения
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/srv/media")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8081")
ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,webp,svg,mp4,webm,mkv,avi,mp3,wav,ogg,flac,aac").split(","))

class MediaScanner:
    """Сканер медиа-файлов"""
    
    def __init__(self, media_root: str, public_base_url: str):
        self.media_root = Path(media_root)
        self.public_base_url = public_base_url.rstrip('/')
        self.magic_mime = magic.Magic(mime=True)
        
        # Создаем необходимые каталоги
        self.index_dir = self.media_root / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # Пути к файлам индекса и кеша
        self.index_file = self.index_dir / "media_links.json"
        self.cache_file = self.index_dir / "scanner_cache.json"
        
        # Загружаем кеш
        self.cache = self.load_cache()
    
    def load_cache(self) -> Dict:
        """Загрузка кеша для инкрементального сканирования"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Не удалось загрузить кеш: {e}")
        
        return {}
    
    def save_cache(self):
        """Сохранение кеша"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Не удалось сохранить кеш: {e}")
    
    def is_media_file(self, filepath: Path) -> bool:
        """Проверка медиа-файла"""
        ext = filepath.suffix.lower().lstrip('.')
        return ext in ALLOWED_EXTENSIONS
    
    def get_file_type(self, filepath: Path, mime_type: str = "") -> str:
        """Определение типа файла"""
        if mime_type:
            if mime_type.startswith('image/'):
                return 'image'
            elif mime_type.startswith('video/'):
                return 'video'
            elif mime_type.startswith('audio/'):
                return 'audio'
        
        ext = filepath.suffix.lower()
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}:
            return 'image'
        elif ext in {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}:
            return 'video'
        elif ext in {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}:
            return 'audio'
        
        return 'other'
    
    def calculate_file_hash(self, filepath: Path) -> str:
        """Вычисление MD5 хеша файла"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Ошибка вычисления хеша {filepath}: {e}")
            return ""
    
    def generate_file_id(self, path: str, size: int, md5: str) -> str:
        """Генерация уникального ID файла"""
        content = f"{path}_{size}_{md5}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def process_file(self, filepath: Path) -> Optional[Dict]:
        """Обработка одного файла"""
        try:
            # Получаем информацию о файле
            stat = filepath.stat()
            relative_path = filepath.relative_to(self.media_root)
            cache_key = str(relative_path)
            
            # Проверяем кеш (если размер и время модификации не изменились)
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                if (cached.get('size') == stat.st_size and 
                    cached.get('mtime') == stat.st_mtime):
                    return cached.get('data')
            
            logger.info(f"Обрабатываем файл: {relative_path}")
            
            # Вычисляем MD5
            md5_hash = self.calculate_file_hash(filepath)
            if not md5_hash:
                return None
            
            # Определяем MIME тип
            try:
                mime_type = self.magic_mime.from_file(str(filepath))
            except Exception:
                mime_type = ""
            
            # Создаем запись
            file_data = {
                "id": self.generate_file_id(str(relative_path), stat.st_size, md5_hash),
                "name": filepath.name,
                "url": f"{self.public_base_url}/{relative_path}",
                "type": self.get_file_type(filepath, mime_type),
                "mime_type": mime_type,
                "size": stat.st_size,
                "path": f"/{relative_path}",
                "md5": md5_hash,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
            # Сохраняем в кеш
            self.cache[cache_key] = {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'data': file_data
            }
            
            return file_data
            
        except Exception as e:
            logger.error(f"Ошибка обработки файла {filepath}: {e}")
            return None
    
    def scan_directory(self, directory: Path) -> List[Dict]:
        """Сканирование каталога"""
        media_files = []
        
        try:
            # Рекурсивно обходим все файлы
            for filepath in directory.rglob("*"):
                # Пропускаем каталоги и служебные файлы
                if filepath.is_dir() or filepath.name.startswith('.'):
                    continue
                
                # Пропускаем индексный каталог
                if "index" in filepath.parts:
                    continue
                
                # Проверяем, что это медиа-файл
                if not self.is_media_file(filepath):
                    continue
                
                # Обрабатываем файл
                file_data = self.process_file(filepath)
                if file_data:
                    media_files.append(file_data)
        
        except Exception as e:
            logger.error(f"Ошибка сканирования каталога {directory}: {e}")
        
        return media_files
    
    def cleanup_cache(self, existing_files: set):
        """Очистка кеша от удаленных файлов"""
        keys_to_remove = []
        for cache_key in self.cache.keys():
            filepath = self.media_root / cache_key
            if not filepath.exists() or str(Path(cache_key)) not in existing_files:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self.cache[key]
            logger.info(f"Удален из кеша: {key}")
    
    def scan_and_index(self) -> Dict:
        """Основной метод сканирования и индексации"""
        start_time = time.time()
        logger.info("Начинаем сканирование медиа-файлов...")
        
        # Сканируем медиа-файлы
        media_files = self.scan_directory(self.media_root)
        
        # Очищаем кеш от удаленных файлов
        existing_files = {file_data['path'].lstrip('/') for file_data in media_files}
        self.cleanup_cache(existing_files)
        
        # Создаем итоговый JSON
        result = {
            "media_files": media_files,
            "total_files": len(media_files),
            "total_size": sum(file_data["size"] for file_data in media_files),
            "last_updated": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
        
        # Сохраняем индекс
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Индекс сохранен: {self.index_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения индекса: {e}")
            raise
        
        # Сохраняем кеш
        self.save_cache()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Сканирование завершено за {elapsed_time:.2f}с. Найдено файлов: {len(media_files)}")
        
        return result

def main():
    """Главная функция"""
    try:
        scanner = MediaScanner(MEDIA_ROOT, PUBLIC_BASE_URL)
        result = scanner.scan_and_index()
        
        print(f"✅ Обработано файлов: {result['total_files']}")
        print(f"✅ Общий размер: {result['total_size'] / (1024*1024):.2f} МБ")
        print(f"✅ Индекс обновлен: {result['last_updated']}")
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()