# AI Agent Guide

## Repository Overview
- `frontend/` is a Nuxt 4 (Vue 3 + TypeScript) app using Tailwind and shadcn/ui.
- `backend/` is a FastAPI service with layered architecture (API → service → repository → persistence).
- Use `docker compose up --build` for the full stack (frontend `:3000`, backend `:8000`).

## Key Commands
- Frontend (run in `frontend/`): `npm run dev`, `npm run build`, `npm run lint`, `npm run format`.
- Backend (run in `backend/`): `ruff check .`, `ruff format .`, `pytest`.
- Docker: `docker compose up --build`, `docker compose down`.

## Coding Conventions
- Keep backend SOLID boundaries: API depends on services, services depend on repositories, repositories depend on persistence.
- Keep DB models in `backend/app/db/models.py` and Pydantic schemas in `backend/app/schemas/`.
- Frontend components live in `frontend/app/components`, pages in `frontend/app/pages`.
- Avoid editing generated artifacts (`node_modules/`, `.output/`, `.nuxt/`, `data/`).

## Environment
- Backend expects `DATABASE_URL`, `CORS_ORIGINS`, `LOG_LEVEL` (see `backend/.env.example`).
- Frontend expects `NUXT_PUBLIC_API_BASE` (see `frontend/.env.example`).

## Testing
- Backend API smoke test: `backend/tests/test_contacts_api.py`.
