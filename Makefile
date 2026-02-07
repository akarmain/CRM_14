.PHONY: up down lint fmt test

up:
	docker compose up --build

down:
	docker compose down

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

fmt:
	cd backend && ruff format .
	cd frontend && npm run format

test:
	cd backend && pytest
