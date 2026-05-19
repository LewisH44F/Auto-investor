.PHONY: up down build logs migrate seed backend-shell db-shell test lint \
        dev-backend dev-frontend install scan restart-worker

# =============================================================================
# AutoInvestor Intelligence System — Makefile
# =============================================================================

## up: Start all services in detached mode
up:
	docker-compose up -d

## down: Stop and remove containers
down:
	docker-compose down

## build: Rebuild all Docker images
build:
	docker-compose build

## logs: Follow logs from all services
logs:
	docker-compose logs -f

## migrate: Run database initialisation / migrations
migrate:
	docker-compose exec backend python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

## seed: Load initial schema SQL into the database
seed:
	docker-compose exec postgres psql -U autoinvestor -d autoinvestor -f /migrations/init_schema.sql

## backend-shell: Open a bash shell in the backend container
backend-shell:
	docker-compose exec backend bash

## db-shell: Open a psql shell in the postgres container
db-shell:
	docker-compose exec postgres psql -U autoinvestor -d autoinvestor

## test: Run the backend test suite with verbose output
test:
	docker-compose exec backend pytest tests/ -v

## lint: Run ruff on backend and ESLint on frontend
lint:
	docker-compose exec backend ruff check app/
	docker-compose exec frontend npm run lint

## dev-backend: Run the backend locally (outside Docker) with hot-reload
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

## dev-frontend: Run the frontend dev server locally (outside Docker)
dev-frontend:
	cd frontend && npm run dev

## install: Install frontend npm dependencies
install:
	cd frontend && npm install

## scan: Trigger a nightly analysis scan manually
scan:
	docker-compose exec backend python -m app.workers.nightly_analysis

## restart-worker: Restart only the background worker service
restart-worker:
	docker-compose restart worker
