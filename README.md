# file-sync

Автоматическая синхронизация медиа-ссылок с Filen.io для VPS-проектов. Метаданные и публичные ссылки в формате JSON для интеграции с сайтом.

## Описание

Этот проект предназначен для автоматической синхронизации медиа-файлов с облачным хранилищем Filen.io. Скрипт создает и поддерживает актуальную базу данных публичных ссылок на медиа-файлы в формате JSON, которую можно использовать для интеграции с веб-сайтами на VPS.

## Структура проекта

```
file-sync/
├── README.md                           # Документация проекта
├── media_links.json                    # База данных медиа-ссылок
├── scripts/
│   └── sync_media.py                   # Основной скрипт синхронизации
└── .github/
    └── workflows/
        └── filen-media-sync.yml        # GitHub Actions workflow
```

## Возможности

- 🔄 Автоматическая синхронизация каждые 6 часов
- 📦 Хранение метаданных в формате JSON
- 🔗 Генерация публичных ссылок на медиа-файлы
- 🤖 Автоматизация через GitHub Actions
- 🔐 Безопасное хранение API ключей через GitHub Secrets

## Настройка

### 1. Установка зависимостей

```bash
pip install requests
```

### 2. Настройка GitHub Secrets

Добавьте следующий секрет в настройках репозитория (Settings → Secrets and variables → Actions):

- `FILEN_API_KEY` - API ключ от Filen.io

### 3. Ручной запуск

Можно запустить синхронизацию вручную:

```bash
export FILEN_API_KEY="your_api_key"
python scripts/sync_media.py
```

## Использование

### Автоматическая синхронизация

GitHub Actions workflow автоматически запускается каждые 6 часов. Также можно запустить workflow вручную через вкладку Actions.

### Формат данных

Файл `media_links.json` содержит информацию о медиа-файлах:

```json
{
  "media_files": [
    {
      "id": "unique_id",
      "name": "filename.jpg",
      "url": "https://filen.io/d/...",
      "type": "image",
      "size": 1234567,
      "uploaded": "2025-10-29T12:00:00"
    }
  ],
  "last_updated": "2025-10-29T12:00:00",
  "version": "1.0"
}
```

## Интеграция с сайтом

Используйте `media_links.json` для получения актуальных ссылок на медиа-файлы:

```javascript
fetch('https://raw.githubusercontent.com/KomarovAI/file-sync/main/media_links.json')
  .then(response => response.json())
  .then(data => {
    console.log('Media files:', data.media_files);
  });
```

## Требования

- Python 3.x
- Аккаунт Filen.io с API ключом
- GitHub account (для автоматизации)

## Лицензия

MIT

## Автор

KomarovAI
