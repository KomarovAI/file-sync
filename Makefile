.PHONY: help build up down logs clean dev test

help: ## Показать это сообщение
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\\033[36m%-15s\\033[0m %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Собрать все образы
	docker-compose build

up: ## Запустить все сервисы
	docker-compose up -d

down: ## Остановить все сервисы
	docker-compose down

logs: ## Показать логи всех сервисов
	docker-compose logs -f

clean: ## Очистить неиспользуемые образы и контейнеры
	docker system prune -f
	docker volume prune -f

dev: ## Запустить в режиме разработки
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

test: ## Запустить тесты
	@echo "Testing API endpoints..."
	@curl -f http://localhost:8081/healthz || echo "❌ Health check failed"
	@curl -f http://localhost:8081/api/media || echo "❌ Media API failed"

status: ## Показать статус сервисов
	docker-compose ps

restart: ## Перезапустить все сервисы
	docker-compose restart

index: ## Запустить индексацию вручную
	docker-compose run --rm indexer python scanner.py

backup: ## Создать бэкап медиа-файлов
	@echo "Creating backup..."
	@docker run --rm -v file-sync_media_data:/data -v $(PWD):/backup alpine tar czf /backup/media-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz -C /data .

shell-api: ## Открыть shell в API контейнере
	docker-compose exec api bash

shell-nginx: ## Открыть shell в Nginx контейнере
	docker-compose exec nginx sh

install: ## Первоначальная настройка
	@echo "Setting up VPS Media Server..."
	@cp .env.example .env
	@echo "✅ Please edit .env file with your settings"
	@echo "✅ Then run: make build && make up"