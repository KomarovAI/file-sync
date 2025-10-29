# VPS Media Server

Самохостинговый медиа-сервер на Docker Compose с REST API для загрузки, индексации и публичной раздачи медиа-файлов через Nginx.

## 🎆 Новая архитектура

Проект полностью переработан для самохостинга на VPS:

- ✅ **Полный контроль** - никаких внешних зависимостей и лимитов
- ✅ **Бесплатные публичные ссылки** - никаких Pro-подписок
- ✅ **Высокая производительность** - раздача через Nginx
- ✅ **Простое развертывание** - Docker Compose одной командой
- ✅ **Автодеплой** - GitHub Actions на VPS

## 🏠 Архитектура

### Компоненты:
- **Nginx** (порт 8081) - раздача статических файлов и reverse proxy
- **FastAPI** (внутренний 8002) - REST API для загрузки и управления
- **Индексатор** - Python скрипт для сканирования и создания JSON каталога

### Порты:
- 🌐 **8081** - публичный HTTP (свободный порт)
- 🔒 **8002** - внутренний API (только в Docker network)

## 🚀 Быстрый старт

### 1. Клонирование ветки
```bash
git clone -b vps-media-server https://github.com/KomarovAI/file-sync.git vps-media-server
cd vps-media-server
```

### 2. Настройка окружения
```bash
cp .env.example .env
# Отредактируйте .env файл
```

**Обязательно настройте:**
```env
PUBLIC_BASE_URL=http://your-vps-ip:8081
API_TOKEN=your-secure-random-token
CORS_ORIGINS=https://yourdomain.com
```

### 3. Запуск
```bash
make build
make up
# или
docker-compose up -d
```

### 4. Проверка
```bash
curl http://localhost:8081/healthz
curl http://localhost:8081/api/media
```

## 📡 API эндпоинты

### Публичные:
```bash
# Каталог медиа-файлов
GET /api/media
GET /api/media?type=image&size_max=10000000

# Статистика
GET /api/stats

# Проверка состояния
GET /healthz

# JSON каталог (совместимость)
GET /index/media_links.json
```

### Защищенные (Bearer токен):
```bash
# Загрузка файла
POST /api/upload
Authorization: Bearer your-api-token
Content-Type: multipart/form-data

# Пример:
curl -X POST \
  -H "Authorization: Bearer your-token" \
  -F "file=@photo.jpg" \
  -F "subdir=images" \
  http://localhost:8081/api/upload
```

## 📁 Структура медиа

```
/srv/media/
├── images/          # Изображения
├── videos/          # Видео файлы
├── audio/           # Аудио файлы
├── docs/            # Документы
├── uploads/         # Загруженные через API
└── index/
    └── media_links.json  # JSON каталог
```

## 📋 Формат JSON каталога

```json
{
  "media_files": [
    {
      "id": "unique_hash",
      "name": "example.jpg",
      "url": "http://your-vps:8081/images/example.jpg",
      "type": "image",
      "mime_type": "image/jpeg",
      "size": 1234567,
      "path": "/images/example.jpg",
      "md5": "hash",
      "created": "2025-10-29T12:00:00Z",
      "modified": "2025-10-29T12:00:00Z"
    }
  ],
  "total_files": 1,
  "total_size": 1234567,
  "last_updated": "2025-10-29T12:00:00Z",
  "version": "1.0"
}
```

## 🔗 Интеграция с сайтом

### JavaScript (полностью совместимо!):
```javascript
// Тот же код, что и раньше, только URL изменился!
const response = await fetch('http://your-vps:8081/index/media_links.json');
const mediaData = await response.json();

mediaData.media_files.forEach(file => {
  if (file.type === 'image') {
    const img = document.createElement('img');
    img.src = file.url;  // Прямая ссылка через Nginx!
    gallery.appendChild(img);
  }
});
```

### Фильтрация через API:
```javascript
// Только изображения
const images = await fetch('http://your-vps:8081/api/media?type=image');

// Файлы меньше 10 МБ
const small = await fetch('http://your-vps:8081/api/media?size_max=10485760');
```

## 🔧 Команды управления

```bash
# Основные
make build          # Собрать образы
make up             # Запустить сервисы
make down           # Остановить
make logs           # Логи

# Мониторинг
make status         # Статус контейнеров
make test           # Проверка API

# Обслуживание
make index          # Ручная индексация
make backup         # Бэкап медиа-файлов
make clean          # Очистка

# Отладка
make shell-api      # Shell в API контейнере
make shell-nginx    # Shell в Nginx
```

## 🔒 Безопасность

- 🔑 **API токен** для загрузки файлов
- 📋 **MIME валидация** загружаемых файлов
- 📁 **Ограничения** размера файлов
- 🌐 **CORS** настройки для доменов
- 🚫 **Блокировка** системных файлов

## 🚀 Автодеплой на VPS

Проект настроен для автоматического деплоя через GitHub Actions.

### Настроенные секреты:
✅ `VPS_HOST` - IP адрес вашего VPS  
✅ `VPS_USER` - пользователь SSH (root)  
✅ `VPS_SSH_KEY` - приватный SSH ключ  
✅ `VPS_PORT` - порт SSH (22)

### Как это работает:
1. 🔄 **Push** в ветку `vps-media-server`
2. 🔧 **GitHub Actions** соединяется по SSH
3. 📦 **Обновляет** код и пересобирает контейнеры
4. ✅ **Проверяет** работоспособность API

### Мануальный деплой:
```bash
# На VPS:
cd /opt/file-sync
git pull origin vps-media-server
docker-compose up -d --build
```

## 📊 Production настройки

### 1. HTTPS
Добавьте SSL сертификаты в nginx.conf или используйте Traefik/Caddy

### 2. Домен
```env
PUBLIC_BASE_URL=https://media.yourdomain.com
```

### 3. Бэкапы
```bash
# Автоматические бэкапы
0 2 * * * cd /opt/file-sync && make backup
```

### 4. Мониторинг
```bash
# Healthcheck
curl http://your-vps:8081/healthz

# Логи
docker-compose logs -f --tail=100
```

## 📜 Миграция с старой версии

Проект **полностью совместим** с существующим кодом:

- ✅ **Тот же формат** media_links.json
- ✅ **Те же поля** в JSON объектах
- ✅ **Просто смените URL** в своем fetch()

Измените только:
```javascript
// Было:
fetch('https://raw.githubusercontent.com/KomarovAI/file-sync/main/media_links.json')

// Стало:
fetch('http://your-vps:8081/index/media_links.json')
```

## 🏆 Преимущества

### Против облачных API:
- ❌ **Filen.io** - Pro-подписка для публичных ссылок
- ✅ **VPS Media Server** - бесплатно и без лимитов!

### Против обычного хостинга:
- ✅ **Полный контроль** над файлами
- ✅ **REST API** для автоматизации
- ✅ **Автоматическая синхронизация**
- ✅ **Простое развертывание**

---

## 🔗 Полезные ссылки

- 📚 [FastAPI документация](https://fastapi.tiangolo.com/)
- 🐳 [Docker Compose гайд](https://docs.docker.com/compose/)
- 🌐 [Nginx конфиг](https://nginx.org/ru/docs/)
- 🔧 [GitHub Actions](https://docs.github.com/actions)

## 🎆 Следующие шаги

- 🔒 **HTTPS** с Let's Encrypt
- 🌍 **CDN** для экономии трафика
- 📊 **Мониторинг** Prometheus + Grafana
- 🗺️ **Web-интерфейс** для управления
- 📦 **MinIO S3** для масштабирования

---

**Лицензия:** MIT | **Автор:** KomarovAI