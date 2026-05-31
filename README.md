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
| Кармаев Андрей Александрович ИНБО-30-25 | Тимлид / Аналитик / Project Lead |
| Кучин Иван Вадимович ЭПБО-01-25 | 1С-разработчик |
| Рахимов Шамиль Рашитович ЭФБО-02-25 | Backend-разработчик (API, БД, KPI) |
| Маркина Майя Витальевна ЭФБО-02-25 | Frontend-разработчик (канбан, аналитика, запросы на возврат, история лида, интеграция с API) |
| Полухина Елизавета Константиновна ЭФБО-02-25 | Frontend-разработчик (стартовая, сессия/роутинг, таблица, модальные окна, базовый API-клиент, CSS) |


## Документация

Единый источник правды по проекту — сайт документации в `docs/` (MkDocs Material). Точка входа: `docs/index.md`.

Ключевые документы:

- описание as-built реализации (фактический код): `docs/06-final-specification/DOC-SPC-003-as-built-implementation.md`;
- интеграция 1С и Python: `docs/05-data-and-integration/DOC-INT-002-1c-python-apache-integration.md` и `DOC-INT-003-1c-python-docker-integration.md`.

Локальный просмотр и сборка:

```bash
python3 -m pip install -r docs-requirements.txt
mkdocs serve     # просмотр на http://127.0.0.1:8000
mkdocs build     # статическая сборка в ./site
```
