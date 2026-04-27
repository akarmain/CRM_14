.PHONY: run test lint format migrate

run:
	uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	uv run alembic upgrade head

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run mypy app tests

format:
	uv run ruff format .
