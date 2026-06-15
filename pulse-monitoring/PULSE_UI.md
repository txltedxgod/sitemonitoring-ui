# Pulse UI — новый фронтенд для Site Monitor

К твоему бэкенду добавлен красивый SPA-дашборд **Pulse**. Ничего из старой
логики не удалено — старый Jinja-дашборд по-прежнему живёт на `/`.

## Что добавлено

| Файл | Что это |
|------|--------|
| `app/api.py` | JSON-API поверх твоих сервисов (`app.services.sites`, `monitor.check_single`). Без дублирования логики БД. |
| `app/static/pulse.html` | Весь фронтенд в одном файле (HTML+CSS+JS, без сборки). |
| `app/main.py` | Подключены CORS, `api_router` и маршрут `/ui`. |

## Как запустить

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Затем открой:

- **http://localhost:8000/ui** — новый дашборд Pulse (автоматически ходит в API того же origin);
- **http://localhost:8000/** — старый Jinja-дашборд (остался как был);
- **http://localhost:8000/docs** — Swagger с новыми `/api/*`.

## API (что отдаёт `app/api.py`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/sites` | Список сайтов + последние проверки (для sparkline/uptime). |
| GET | `/api/sites/{id}` | Детали сайта + история проверок (до 200). |
| POST | `/api/sites` | Добавить сайт (`{name,url,interval_minutes,expected_status}`). |
| POST | `/api/sites/{id}/check-now` | Проверить сейчас. |
| DELETE | `/api/sites/{id}` | Удалить сайт. |

Валидация и проверки идут через твой же сервисный слой, поэтому поведение идентично
старому дашборду и APScheduler-тикам.

## Режимы фронтенда

- Открыт по **http://** (т.е. через `/ui`) — работает на реальном API того же origin.
- Открыт как **file://** (двойной клик по `pulse.html`) — демо-режим с мок-данными.
- Можно явно задать/сбросить адрес API в разделе «Настройки» внутри дашборда.
