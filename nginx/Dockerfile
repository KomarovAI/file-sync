FROM nginx:alpine

# Копируем конфигурацию
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Устанавливаем curl для healthcheck
RUN apk add --no-cache curl

# Создаем каталог для статических файлов
RUN mkdir -p /srv/media

EXPOSE 80