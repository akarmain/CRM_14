<div align="center">

# CRM_14 — мини-CRM «Лиды и воронка продаж»

Учебный MVP CRM-системы: ведение лидов, движение по стадиям воронки,
ролевой доступ, импорт/экспорт и аналитика продаж.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white)](https://vite.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

🌐 **Живое демо:** [1c-demo.akarmain.ru](https://1c-demo.akarmain.ru/leads/table) &nbsp;·&nbsp; 📺 **Видео-демо:** [YouTube](https://youtu.be/HjYyM2PxYMQ)

</div>

---

## О проекте

Компании теряют лидов из-за разрозненных данных и непрозрачной воронки продаж.
**CRM_14** — учебный MVP, который централизует работу с лидами: фиксирует каждую
стадию, историю переходов и комментарии, считает базовые KPI воронки и разграничивает
доступ по ролям (менеджер, руководитель отдела продаж, аналитик).

Проект относится к кейсу №3 «CRM-мини: лиды и воронка продаж».

## 📺 Демонстрация

<div align="center">

[![Видео-демо CRM_14](https://img.youtube.com/vi/HjYyM2PxYMQ/maxresdefault.jpg)](https://youtu.be/HjYyM2PxYMQ)

▶️ Смотреть видео-демо на YouTube

</div>

## Возможности

- 🧩 **Лиды и воронка** — создание лидов, движение по стадиям `new → qualified → proposal → won/lost`, история стадий с длительностью.
- 🔐 **Роли** — менеджеры (только свои лиды), руководитель отдела продаж (всё + управление), аналитик (read-only + отчёты).
- 🔄 **Возвраты стадий** — менеджер создаёт заявку, РОП одобряет/отклоняет с комментарием.
- 📋 **Канбан и таблица** — два представления лидов, фильтры по владельцу, источнику и периоду.
- 📥 **Импорт / 📤 экспорт** — загрузка лидов из CSV/XLSX, выгрузка в CSV и XLSX (с листом аналитики и графиками).
- 📊 **Аналитика** — конверсии между стадиями и средняя длительность стадий.
- 📝 **Аудит** — журнал ключевых действий по лидам.
- 🗄️ **Гибкое хранилище** — PostgreSQL, in-memory или внешний 1С через HTTP-адаптер (`STORAGE_MODE`).

<!-- СКРИНШОТЫ: раскомментируй этот блок после того, как положишь PNG в docs/assets/screenshots/ (имена см. в HOWTO.txt)
## Скриншоты

| Выбор роли | Таблица лидов | Канбан |
|:---:|:---:|:---:|
| ![Выбор роли](docs/assets/screenshots/01-role-select.png) | ![Таблица лидов](docs/assets/screenshots/02-leads-table.png) | ![Канбан](docs/assets/screenshots/03-kanban.png) |
| **История лида** | **Отчёт по воронке** | **Запросы на возврат** |
| ![История лида](docs/assets/screenshots/04-lead-history.png) | ![Отчёт](docs/assets/screenshots/05-reports.png) | ![Запросы на возврат](docs/assets/screenshots/06-return-requests.png) |
-->
<!-- TODO: добавить скриншоты интерфейса (см. docs/assets/screenshots/HOWTO.txt) -->

## Технологии

| Слой | Стек |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy (async), Alembic, Uvicorn |
| Frontend | React 19, Vite 7, React Router 7 |
| Данные | PostgreSQL 17 · in-memory · 1С (HTTP) |
| Инфраструктура | Docker Compose, `uv`, `npm` |

Backend построен по clean architecture: `domain` / `application` / `infrastructure` / `interface`.

## Быстрый старт

### Вариант 1 — Docker (рекомендуется)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: <http://localhost:5173>
- Backend API + Swagger: <http://localhost:8000/docs>

По умолчанию поднимается PostgreSQL, backend сам применяет миграции при старте.

### Вариант 2 — вручную

```bash
# Backend
cd backend
uv sync
cp .env.example .env        # STORAGE_MODE=memo — запуск без БД
make run                    # http://localhost:8000/docs

# Frontend (в отдельном терминале)
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

Подробности: [`backend/README.md`](backend/README.md) и [`frontend/README.md`](frontend/README.md).

## Демо-сценарий

1. Открыть приложение, выбрать роль `manager_1`.
2. Создать лид → он появляется в таблице и канбане в стадии «Новый».
3. Перевести лид в `qualified` с комментарием, открыть историю.
4. Создать заявку на возврат стадии.
5. Сменить роль на `sales_head`, в «Запросах» одобрить возврат.
6. Открыть «Отчёты» — конверсии и средняя длительность стадий.
7. Выполнить экспорт в CSV/XLSX.
8. Сменить роль на `analyst` — доступ только на чтение.

## Документация

Единый источник правды — сайт документации в [`docs/`](docs/index.md) (MkDocs Material).

```bash
python3 -m pip install -r docs-requirements.txt
mkdocs serve     # http://127.0.0.1:8000
```

Ключевые документы:

- [Фактическая реализация (as-built)](docs/06-final-specification/DOC-SPC-003-as-built-implementation.md)
- [Интеграция 1С и Python (Apache)](docs/05-data-and-integration/DOC-INT-002-1c-python-apache-integration.md) · [(Docker)](docs/05-data-and-integration/DOC-INT-003-1c-python-docker-integration.md)
- [Команда проекта и роли](docs/00-governance/DOC-GOV-003-team-roles-and-communication-plan.md)

## Команда

| ФИО | Группа | Роль |
| --- | --- | --- |
| Кармаев Андрей Александрович | ИНБО-30-25 | Тимлид / Аналитик / Project Lead |
| Рахимов Шамиль Рашитович | ЭФБО-02-25 | Backend-разработчик (API, БД, KPI) |
| Маркина Майя Витальевна | ЭФБО-02-25 | Frontend (канбан, аналитика, запросы на возврат, история лида, интеграция с API) |
| Полухина Елизавета Константиновна | ЭФБО-02-25 | Frontend (стартовая, сессия/роутинг, таблица, модальные окна, базовый API-клиент, CSS) |
| Кучин Иван Вадимович | ЭПБО-01-25 | 1С-разработчик (1С-контур, HTTP-методы, связь с Python) |

---

<div align="center">
Учебный проект. Не является промышленной CRM-платформой.
</div>
