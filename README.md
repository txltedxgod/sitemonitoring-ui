# Pulse — Site Monitoring

**Pulse** — full-stack сервис мониторинга доступности сайтов: асинхронный бэкенд на **FastAPI**, который проверяет URL по расписанию и шлёт алерты в Telegram, и современный одностраничный дашборд **Pulse** поверх него.

> Стек: **FastAPI** · **APScheduler** · **SQLAlchemy 2.0 (async)** · **SQLite** · **httpx** · ванильный **HTML/CSS/JS** фронтенд (без сборки) · **Docker**.
Демо-версия доступна по ссылке: _https://txltedxgod.github.io/sitemonitoring-ui/_
---

## ✨ Возможности

### Фронтенд (Pulse UI)
- 📊 **Дашборд** со сводкой: всего сайтов / онлайн / недоступны / среднее время ответа.
- 🟢 **Живые статусы** с индикаторами и **sparkline** на каждой карточке.
- 📈 **Детали сайта**: аптайм за 24ч / 7д / всё время, график времени ответа, таблица истории проверок.
- ➕ Добавление сайта с валидацией, удаление с подтверждением, кнопка «Проверить сейчас».
- 🎨 Тёмная/светлая темы, адаптив, toast-уведомления, авто-обновление каждые 30 c.
- ⚡ Весь фронтенд — **один файл** `app/static/pulse.html`, без сборки и зависимостей.

### Бэкенд
- ⏱️ **Фоновый планировщик** (APScheduler): проверяет каждый сайт раз в N минут.
- 🔔 **Telegram-алерты** при падении и восстановлении (только на смену статуса, без спама).
- 📜 **История проверок**: время, up/down, HTTP-код, время ответа, текст ошибки.
- 📊 **Статистика аптайма** за 24ч / 7д / всё время + среднее время ответа.
- 🐳 **Docker**: `Dockerfile` + `docker-compose.yml`.

---

## 🚀 Быстрый старт

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Открой:

| URL | Что это |
|-----|--------|
| <http://localhost:8000/ui> | **Pulse** — новый дашборд |
| <http://localhost:8000/> | Классический Jinja-дашборд |
| <http://localhost:8000/docs> | Swagger / OpenAPI |

Или через Docker:

```bash
docker compose up --build
```

> 💡 Файл `app/static/pulse.html` можно открыть и просто двойным кликом — он запустится в **демо-режиме** с мок-данными, без бэкенда.

---

## 🔌 API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/sites` | Список сайтов + последние проверки |
| GET | `/api/sites/{id}` | Детали сайта + история проверок |
| POST | `/api/sites` | Добавить сайт |
| POST | `/api/sites/{id}/check-now` | Проверить сейчас |
| DELETE | `/api/sites/{id}` | Удалить сайт |

JSON-API (`app/api.py`) построен поверх того же сервисного слоя, что и классический дашборд — одна логика, без дублирования.

---

## 🗂 Структура

```
app/
├─ api.py            # JSON-API для фронтенда Pulse
├─ main.py           # точка входа FastAPI (CORS, роутеры, /ui)
├─ models.py         # SQLAlchemy: Site, Check
├─ database.py       # async engine + сессии
├─ scheduler.py      # APScheduler-тик
├─ routers/          # классический Jinja-дашборд
├─ services/         # checker, monitor, sites, telegram
└─ static/
   └─ pulse.html     # весь фронтенд Pulse (один файл)
```

Подробнее про фронтенд и режимы — в [`PULSE_UI.md`](PULSE_UI.md).

---

## ⚙️ Настройка

Скопируй `.env.example` → `.env` и при желании укажи Telegram-бота:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
TICK_SECONDS=60
DEFAULT_INTERVAL_MINUTES=5
```

---

## 📄 Лицензия

MIT — см. [LICENSE](LICENSE).
