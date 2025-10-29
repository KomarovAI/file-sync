FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    file \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем supercronic для cron в контейнере
RUN curl -fsSL https://github.com/aptible/supercronic/releases/download/v0.2.26/supercronic-linux-amd64 \
    -o /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic

# Создаем пользователя приложения
RUN useradd --create-home --shell /bin/bash app

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY indexer/requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY indexer/ .

# Создаем каталог для медиа
RUN mkdir -p /srv/media && chown -R app:app /srv/media

# Создаем crontab
RUN echo "*/10 * * * * /usr/local/bin/python /app/scanner.py" > /app/crontab

# Переключаемся на пользователя приложения
USER app

# Команда запуска (supercronic с crontab)
CMD ["supercronic", "/app/crontab"]