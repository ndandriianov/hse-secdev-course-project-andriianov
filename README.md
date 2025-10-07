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

### Аутентификация и пользователи

- `POST /auth/register` — регистрация нового пользователя
- `POST /auth/login` — вход, выдача `access_token` / `refresh_token`
  - при ≥ 5 неуспешных логинах за 3 мин — временная блокировка (5 мин)
- `POST /auth/logout` — отзыв текущего токена
- `POST /auth/refresh` — обновление access-токена по refresh-токену
- `POST /auth/change-password` — смена пароля (влечёт отзыв всех активных сессий ≤ 5 мин)
- `GET /auth/me` — получить профиль текущего пользователя

---

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

---

### Аудит и логи
- `GET /audit` — получить события аудита (только для владельца или администратора)
  - фиксируются ≥ 80 % критичных действий (auth, изменение данных, удаление и т. д.)
  - создаются ≤ 15 сек после операции

### Администрирование и мониторинг *(опционально)*
- `GET /health` — проверка состояния сервиса
- `GET /metrics` — базовые метрики (время отклика, количество пользователей, целей и т. д.)

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
