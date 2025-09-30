# OKR Tracker

**Описание:** личные цели и ключевые результаты

## Стек

- Python
- FastAPI  
- Postgres
- Pytest  

## Сущности
- **User**  
- **Objective**: `title`, `period`  
- **KeyResult**: `title`, `metric`, `progress`  

## Эндпоинты

### Objectives
- `GET /objectives` — получить список своих целей  
- `POST /objectives` — создать новую цель  
- `PUT /objectives/{id}` — обновить существующую цель  
- `DELETE /objectives/{id}` — удалить цель  

### Key Results
- `GET /key-results` — получить список ключевых результатов  
- `POST /key-results` — создать новый ключевой результат  
- `PUT /key-results/{id}` — обновить ключевой результат  
- `DELETE /key-results/{id}` — удалить ключевой результат  

### Статистика
- `GET /stats` — получить статистику прогресса по целям и ключевым результатам  

## Безопасность и контроль доступа
- **AuthN/AuthZ** — аутентификация и авторизация  
- **owner-only** — доступ только для владельца  
- **validation(periods)** — проверка корректности периодов

## Быстрый старт
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
uvicorn app.main:app --reload
```

## Ритуал перед PR
```bash
ruff check --fix .
black .
isort .
pytest -q
pre-commit run --all-files
```

## Тесты
```bash
pytest -q
```

## Контейнеры
```bash
docker build -t secdev-app .
docker run --rm -p 8000:8000 secdev-app
# или
docker compose up --build
```
