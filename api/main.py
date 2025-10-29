from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import json
import hashlib
import magic
import aiofiles
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import shutil

app = FastAPI(
    title="VPS Media Server API",
    description="REST API для управления медиа-файлами",
    version="1.0.0"
)

# Настройки из переменных окружения
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/srv/media")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8081")
API_TOKEN = os.getenv("API_TOKEN")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "100")) * 1024 * 1024  # MB в байты
ALLOWED_EXTENSIONS = set(os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,webp,svg,mp4,webm,mkv,avi,mp3,wav,ogg,flac,aac").split(","))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != [''] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)

# Безопасность
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not API_TOKEN:
        raise HTTPException(status_code=500, detail="API_TOKEN не настроен")
    
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    
    return credentials.credentials

def is_media_file(filename: str, mime_type: str = "") -> bool:
    """Проверка медиа-файла по расширению и MIME типу"""
    ext = Path(filename).suffix.lower().lstrip('.')
    
    if ext in ALLOWED_EXTENSIONS:
        return True
    
    if mime_type:
        return any(mime_type.startswith(prefix) for prefix in ["image/", "video/", "audio/"])
    
    return False

def get_file_type(filename: str, mime_type: str = "") -> str:
    """Определение типа файла"""
    if mime_type:
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
    
    ext = Path(filename).suffix.lower()
    if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'}:
        return 'image'
    elif ext in {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'}:
        return 'video'
    elif ext in {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}:
        return 'audio'
    
    return 'other'

def load_media_index() -> dict:
    """Загрузка JSON индекса медиа-файлов"""
    index_path = Path(MEDIA_ROOT) / "index" / "media_links.json"
    
    if not index_path.exists():
        return {
            "media_files": [],
            "total_files": 0,
            "total_size": 0,
            "last_updated": "",
            "version": "1.0"
        }
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {
            "media_files": [],
            "total_files": 0,
            "total_size": 0,
            "last_updated": "",
            "version": "1.0"
        }

@app.get("/healthz")
async def health_check():
    """Проверка состояния сервиса"""
    return {"status": "ok", "service": "media-api", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/media")
async def get_media_index(
    type: Optional[str] = Query(None, description="Фильтр по типу: image, video, audio, other"),
    ext: Optional[str] = Query(None, description="Фильтр по расширению"),
    size_min: Optional[int] = Query(None, description="Минимальный размер в байтах"),
    size_max: Optional[int] = Query(None, description="Максимальный размер в байтах"),
    path_prefix: Optional[str] = Query(None, description="Префикс пути")
):
    """Получение каталога медиа-файлов с фильтрами"""
    data = load_media_index()
    files = data["media_files"]
    
    # Применяем фильтры
    if type:
        files = [f for f in files if f.get("type") == type]
    
    if ext:
        files = [f for f in files if f.get("name", "").lower().endswith(f".{ext.lower()}")]
    
    if size_min is not None:
        files = [f for f in files if f.get("size", 0) >= size_min]
    
    if size_max is not None:
        files = [f for f in files if f.get("size", 0) <= size_max]
    
    if path_prefix:
        files = [f for f in files if f.get("path", "").startswith(path_prefix)]
    
    return {
        "media_files": files,
        "total_files": len(files),
        "total_size": sum(f.get("size", 0) for f in files),
        "filtered": len(files) != len(data["media_files"]),
        "last_updated": data.get("last_updated", ""),
        "version": data.get("version", "1.0")
    }

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    subdir: str = Query("uploads", description="Подкаталог для сохранения"),
    token: str = Depends(verify_token)
):
    """Загрузка медиа-файла"""
    
    # Проверка размера файла
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"Файл слишком большой. Максимум: {MAX_FILE_SIZE // (1024*1024)} МБ")
    
    # Читаем содержимое для проверки MIME
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"Файл слишком большой. Максимум: {MAX_FILE_SIZE // (1024*1024)} МБ")
    
    # Определяем MIME тип
    mime_type = magic.from_buffer(content, mime=True)
    
    # Проверяем, что это медиа-файл
    if not is_media_file(file.filename, mime_type):
        raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла")
    
    # Создаем безопасный путь
    safe_subdir = subdir.replace("..", "").strip("/")
    dest_dir = Path(MEDIA_ROOT) / safe_subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Генерируем уникальное имя файла если нужно
    dest_path = dest_dir / file.filename
    counter = 1
    original_stem = Path(file.filename).stem
    original_suffix = Path(file.filename).suffix
    
    while dest_path.exists():
        new_name = f"{original_stem}_{counter}{original_suffix}"
        dest_path = dest_dir / new_name
        counter += 1
    
    # Сохраняем файл
    try:
        async with aiofiles.open(dest_path, 'wb') as f:
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {str(e)}")
    
    # Генерируем публичную ссылку
    relative_path = str(dest_path.relative_to(Path(MEDIA_ROOT)))
    public_url = f"{PUBLIC_BASE_URL.rstrip('/')}/{relative_path}"
    
    return {
        "success": True,
        "filename": dest_path.name,
        "url": public_url,
        "path": f"/{relative_path}",
        "size": len(content),
        "mime_type": mime_type,
        "type": get_file_type(dest_path.name, mime_type),
        "message": "Файл успешно загружен"
    }

@app.get("/api/stats")
async def get_stats():
    """Статистика медиа-хранилища"""
    data = load_media_index()
    
    # Группировка по типам
    stats_by_type = {}
    for file in data["media_files"]:
        file_type = file.get("type", "other")
        if file_type not in stats_by_type:
            stats_by_type[file_type] = {"count": 0, "size": 0}
        stats_by_type[file_type]["count"] += 1
        stats_by_type[file_type]["size"] += file.get("size", 0)
    
    return {
        "total_files": data.get("total_files", 0),
        "total_size": data.get("total_size", 0),
        "total_size_mb": round(data.get("total_size", 0) / (1024*1024), 2),
        "by_type": stats_by_type,
        "last_updated": data.get("last_updated", "")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)