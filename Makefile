.PHONY: up down logs bootstrap test lint fmt web

up:            ## sobe toda a stack
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api worker

bootstrap:     ## cria organização, projeto e API key de desenvolvimento
	docker compose run --rm api python -m app.cli bootstrap --org "Dev"

test:
	cd backend && pytest

lint:
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run typecheck

fmt:
	cd backend && ruff check --fix . && ruff format .

web:
	cd frontend && npm run dev
