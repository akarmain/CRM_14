# Backend: локальный запуск

## Требования

- `Python 3.12+`
- `uv` (менеджер окружения и зависимостей)

Проверка:

```bash
python3 --version
uv --version
```

## Установка зависимостей

```bash
cd backend
uv sync
```

## Переменные окружения

Создай локальный `.env` из шаблона:

```bash
cp .env.example .env
```

По умолчанию:
- `STORAGE_MODE=memo`
- `LOG_LEVEL=INFO`

## Запуск сервера

```bash
cd backend
make run
```

Сервер:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Тесты и проверки

```bash
cd backend
make test
make lint
```

## Частые проблемы

Если ошибка вида `Failed to spawn: uvicorn`, обычно сломан shebang в старом `.venv` после перемещения проекта.

Исправление:

```bash
cd backend
rm -rf .venv
uv sync
make run
```
