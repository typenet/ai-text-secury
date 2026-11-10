.PHONY: help env up down logs ps api-key test lint fmt web \
	prod-up prod-down prod-logs prod-ps backup restore-db

PROD = docker compose -f docker-compose.yml -f docker-compose.prod.yml
BACKUP_DIR ?= backups

help:          ## lista os comandos
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

env:           ## cria o .env a partir do exemplo (não sobrescreve)
	@test -f .env || cp .env.example .env

# ---------- dev local ----------
up: env       ## sobe a stack de dev (portas em localhost)
	docker compose up -d --build

down:          ## para a stack (os dados ficam nos volumes)
	docker compose down

logs:          ## acompanha logs da API e do worker
	docker compose logs -f api worker

ps:            ## estado e saúde dos serviços
	docker compose ps

api-key:       ## gera mais uma API key (org nova)
	docker compose run --rm api python -m app.cli bootstrap --org "$${ORG:-Dev}"

test:
	cd backend && pytest

lint:
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run typecheck

fmt:
	cd backend && ruff check --fix . && ruff format .

web:
	cd frontend && npm run dev

# ---------- produção (VPS) ----------
prod-up:       ## sobe a stack de produção com HTTPS (Caddy)
	$(PROD) up -d --build

prod-down:
	$(PROD) down

prod-logs:
	$(PROD) logs -f --tail=200

prod-ps:
	$(PROD) ps

backup:        ## dump do Postgres + cópia do volume do storage em ./backups
	@mkdir -p $(BACKUP_DIR)
	$(PROD) exec -T postgres sh -c 'pg_dump -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -Fc' \
		> $(BACKUP_DIR)/db-$$(date +%Y%m%d-%H%M%S).dump
	docker run --rm -v ai-text-secury_storagedata:/data:ro -v "$$(pwd)/$(BACKUP_DIR)":/backup \
		alpine:3 tar czf /backup/storage-$$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@ls -lh $(BACKUP_DIR) | tail -n 4

restore-db:    ## restaura um dump: make restore-db FILE=backups/db-....dump
	@test -n "$(FILE)" || (echo "use: make restore-db FILE=backups/arquivo.dump" && exit 1)
	$(PROD) exec -T postgres sh -c 'pg_restore -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" --clean --if-exists' < $(FILE)
