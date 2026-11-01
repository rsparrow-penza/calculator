# Калькулятор 🧮

Моё первое веб-приложение: калькулятор с историей вычислений в базе данных.

## Стек

| Слой | Технологии |
|---|---|
| Фронтенд | React 19 + Vite |
| Бэкенд | Python 3 + Flask |
| База данных | SQLite |

## Как это работает

Клики по кнопкам собирают арифметическое выражение в React-состоянии.
По нажатию «=» запрос `POST /api/calculate` уходит на Flask: он безопасно
вычисляет выражение, сохраняет его в таблицу `history` в SQLite и возвращает
результат. Панель истории подгружается с `GET /api/history`.

Vite проксирует `/api`-запросы на `http://localhost:5001`, поэтому CORS-проблем нет.

## Запуск

Терминал 1 — бэкенд:

```bash
cd backend
pip3 install -r requirements.txt
python3 app.py
```

Терминал 2 — фронтенд:

```bash
cd frontend
npm install
npm run dev
```

Открыть <http://localhost:5173>

## Запуск в Docker (продакшен-режим)

Нужен установленный [Docker](https://docs.docker.com/get-started/get-docker/).
Из корня проекта одной командой собираются оба контейнера и поднимаются:

```bash
docker compose up -d --build
```

- **frontend** — nginx раздаёт собранный React и проксирует `/api` на бэкенд;
- **backend** — Flask за gunicorn; база SQLite лежит в Docker-томе `dbdata`
  и переживает пересборку контейнеров.

Калькулятор доступен на <http://localhost>. Остановка — `docker compose down`.

## Деплой на сервер (Timeweb Cloud и любой VPS)

```bash
# на сервере (Ubuntu 24.04)
curl -fsSL https://get.docker.com | sh
git clone https://github.com/rsparrow-penza/calculator.git
cd calculator
docker compose up -d --build
```

Сайт будет доступен по IP сервера: `http://<IP-сервера>`

## Управление

- Кнопки на экране или клавиатура: цифры, `+ - * / ( ) .`, `Enter` — равно,
  `Backspace` — стереть, `Esc` — очистить.
- Каждое успешное вычисление сохраняется в базу.
- «Очистить» в панели истории удаляет все записи (`DELETE /api/history`).
