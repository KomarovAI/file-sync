FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    file \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя приложения
RUN useradd --create-home --shell /bin/bash app

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY api/requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY api/ .

# Создаем каталог для медиа
RUN mkdir -p /srv/media && chown -R app:app /srv/media

# Переключаемся на пользователя приложения
USER app

# Открываем порт
EXPOSE 8002

# Команда запуска
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]