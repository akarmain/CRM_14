# CRM_14

Интеграционная ветка проекта, в которой объединены:

- backend и монорепа из `origin/dev/rakhimovsr`
- standalone React/Vite frontend из `origin/front`

Проект представляет собой учебную MVP-версию mini-CRM для работы с лидами. В репозитории сейчас сосуществуют backend на FastAPI и frontend-части из разных веток, чтобы можно было дальше сводить backend и frontend в одном месте.

## Структура

- `backend/` — backend на `Python/FastAPI`
- `frontend/` — frontend из ветки `origin/dev/rakhimovsr` на `Nuxt/Vue`
- `src/`, `public/`, `package.json`, `vite.config.js` — frontend из ветки `origin/front` на `React/Vite`

## Backend

Краткий запуск:

1. Перейти в `backend`
2. Выполнить `uv sync`
3. Запустить `make run`
4. Проверить `http://localhost:8000/docs`

Подробности: `backend/README.md`

## Frontend

В репозитории сейчас две frontend-реализации:

- `frontend/` — Nuxt/Vue приложение из backend-ориентированной ветки
- корневой React/Vite клиент из ветки `front`

Для React/Vite клиента:

```bash
npm install
npm run dev
```

## Стек

- Backend: `Python 3.12+`, `FastAPI`, `Uvicorn`, `Pydantic v2`
- Frontend (`frontend/`): `Nuxt`, `Vue 3`, `TypeScript`, `Tailwind CSS`
- Frontend (корень репозитория): `React 19`, `Vite 7`, `react-router-dom`

## Команда проекта

| ФИО | Роль |
| --- | --- |
| Кармаев Андрей Александрович ИНБО-30-25 | Аналитик / Project Lead |
| Кучин Иван Вадимович ЭПБО-01-25 | 1С-разработчик |
| Рахимов Шамиль Рашитович ЭФБО-02-25 | Full-stack (UI) |
| Маркина Майя Витальевна ЭФБО-02-25 | Full-stack (API) |
| Полухина Елизавета Константиновна ЭФБО-02-25 | Full-stack (Data / KPI) |
