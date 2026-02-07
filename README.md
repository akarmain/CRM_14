# leetbook

Контактная книжка (Telegram Mini App) с Nuxt 4 + FastAPI.

## Быстрый старт (Docker)
```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Проверка API: `curl http://localhost:8000/api/contacts`

## Локальная разработка
Frontend (из `frontend/`):
```bash
npm install
npm run dev
```

Backend (из `backend/`):
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
alembic upgrade head
python -m app.db.seed
uv run main.py
```

Если используешь только `uv`, достаточно:
```bash
uv run alembic -c alembic.ini upgrade head
uv run python -m app.db.seed
uv run main.py
```

По умолчанию CORS открыт (`CORS_ORIGINS=*`). Чтобы ограничить доступ, установи `CORS_ORIGINS=http://localhost:3000,http://192.168.0.243:3000` в `.env`.

## Архитектура
- Backend слои: API → service → repository → persistence (`backend/app/*`).
- Frontend страницы в `frontend/app/pages`, API-клиент в `frontend/app/lib/api.ts`.
