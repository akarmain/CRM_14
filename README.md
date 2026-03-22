# CRM_14

Интеграционная ветка проекта, в которой backend из `origin/dev/rakhimovsr` объединён с React/Vite frontend из `origin/front`.

Проект представляет собой учебную MVP-версию mini-CRM для работы с лидами. В этой сборке backend и frontend разложены по отдельным каталогам без дублирующихся frontend-реализаций.

## Структура

- `backend/` — backend на `Python/FastAPI`
- `frontend/` — frontend на `React/Vite`

## Backend

Краткий запуск:

1. Перейти в `backend`
2. Выполнить `uv sync`
3. Запустить `make run`
4. Проверить `http://localhost:8000/docs`

Подробности: `backend/README.md`

## Frontend

Для frontend:

```bash
cd frontend
npm install
npm run dev
```

## Стек

- Backend: `Python 3.12+`, `FastAPI`, `Uvicorn`, `Pydantic v2`
- Frontend (`frontend/`): `React 19`, `Vite 7`, `react-router-dom`

## Команда проекта

| ФИО | Роль |
| --- | --- |
| Кармаев Андрей Александрович ИНБО-30-25 | Аналитик / Project Lead |
| Кучин Иван Вадимович ЭПБО-01-25 | 1С-разработчик |
| Рахимов Шамиль Рашитович ЭФБО-02-25 | Full-stack (UI) |
| Маркина Майя Витальевна ЭФБО-02-25 | Full-stack (API) |
| Полухина Елизавета Константиновна ЭФБО-02-25 | Full-stack (Data / KPI) |
