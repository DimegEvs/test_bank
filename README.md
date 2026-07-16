# Test Bank API

REST API для банковской системы: управление пользователями, счетами и обработка платежей через вебхуки.

## Технологии

- **FastAPI** — асинхронный веб-фреймворк
- **SQLAlchemy 2.0 (async)** — ORM с asyncpg
- **PostgreSQL 16** — база данных
- **Alembic** — миграции
- **JWT (HttpOnly Cookie)** — аутентификация
- **Jinja2** — шаблоны для UI
- **Docker / Docker Compose** — контейнеризация

## Возможности

- Регистрация и вход пользователей (JWT в HttpOnly cookie)
- Управление профилем, счетами и просмотр истории платежей
- Админ-панель: управление всеми пользователями и счетами
- Обработка платёжных вебхуков с проверкой SHA256-подписи и идемпотентностью
- Веб-интерфейс (SPA) на vanilla JS

## Структура проекта

```
test_bank/
├── app/
│   ├── config.py          # Настройки (Pydantic Settings, .env)
│   ├── main.py            # Точка входа FastAPI
│   ├── database.py        # Async engine и сессии
│   ├── dependencies.py    # Зависимости: текущий пользователь, админ
│   ├── security.py        # JWT, хеширование паролей, подписи
│   ├── models/            # SQLAlchemy-модели (User, Account, Payment)
│   ├── schemas/           # Pydantic-схемы запросов и ответов
│   ├── services/          # Сервисный слой (BaseService, CRUD)
│   └── router/            # Роутеры (auth, users, admin, webhook)
├── migrations/            # Alembic-миграции
├── templates/             # HTML-шаблон UI
├── tests/                 # pytest-тесты (31 тест)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── pytest.ini
```

## Тестовые пользователи по умолчанию

Создаются автоматически при выполнении миграции `alembic upgrade head`:

| Роль    | Email            | Пароль       | ID |
|---------|------------------|--------------|----|
| user    | user@test.com    | userpass     | 1  |
| admin   | admin@test.com   | adminpass    | 2  |

У тестового пользователя (ID 1) также создан счёт (ID 1, баланс 0.00).

---

## Запуск через Docker Compose

### Требования

- Docker 24+
- Docker Compose v2+

### Шаги

```bash
# 1. Сборка и запуск
docker compose up --build

# 2. Проверка (в другом терминале)
curl http://localhost:8000/docs
```



После запуска доступны:
- **UI**: http://localhost:8000
- **Swagger docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Остановить:

```bash
docker compose down          # остановить контейнеры
docker compose down -v       # остановить + удалить volume с БД
```

---

## Запуск без Docker

### Требования

- Python 3.11+
- PostgreSQL 16+

### Шаги

```bash
# 1. Создать виртуальное окружение
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Создать базу данных в PostgreSQL
psql -U postgres -c "CREATE DATABASE test_bank;"

# 4. Скопировать .env.example в .env и при необходимости изменить значения
cp .env.example .env

# 5. Применить миграции
alembic upgrade head

# 6. Запустить сервер
uvicorn app.main:app --reload
```

После запуска доступны:
- **UI**: http://localhost:8000
- **Swagger docs**: http://localhost:8000/docs

---

## Конфигурация (.env)

Все настройки загружаются из файла `.env` (см. `.env.example`):

| Переменная                | Описание                              | Значение по умолчанию |
|---------------------------|---------------------------------------|-----------------------|
| `DATABASE_URL`            | URL БД (async, asyncpg)              | —                     |
| `DATABASE_URL_SYNC`       | URL БД (sync, psycopg2, для Alembic) | —                     |
| `JWT_SECRET_KEY`          | Секрет для подписи JWT               | —                     |
| `JWT_ALGORITHM`           | Алгоритм JWT                          | HS256                 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена (минуты)       | 60                    |
| `PAYMENT_SECRET_KEY`      | Секретный ключ для подписи вебхука   | —                     |
| `COOKIE_NAME`             | Имя cookie с токеном                  | access_token          |
| `COOKIE_SECURE`           | Флаг Secure (только HTTPS)           | false                 |
| `COOKIE_SAMESITE`         | Политика SameSite                     | lax                   |

---

## API эндпоинты

### Auth (`/api/auth`)

| Метод | Путь       | Описание                          | Доступ     |
|-------|------------|-----------------------------------|------------|
| POST  | `/register`| Регистрация нового пользователя   | Публичный  |
| POST  | `/login`   | Вход, установка JWT в cookie      | Публичный  |
| POST  | `/logout`  | Выход, удаление cookie            | Публичный  |

### Users (`/api/users`)

| Метод | Путь                  | Описание                          | Доступ |
|-------|-----------------------|-----------------------------------|--------|
| GET   | `/me`                 | Профиль текущего пользователя     | User+  |
| GET   | `/me/accounts`        | Список счетов                     | User+  |
| POST  | `/me/accounts`        | Создать счёт                      | User+  |
| GET   | `/me/accounts/{id}`   | Получить счёт по ID               | User+  |
| DELETE| `/me/accounts/{id}`   | Удалить счёт                      | User+  |
| GET   | `/me/payments`        | История платежей                  | User+  |

### Admin (`/api/admin`)

| Метод | Путь                        | Описание                        | Доступ |
|-------|-----------------------------|---------------------------------|--------|
| GET   | `/me`                       | Профиль администратора          | Admin  |
| GET   | `/users`                    | Список всех пользователей       | Admin  |
| POST  | `/users`                    | Создать пользователя            | Admin  |
| PUT   | `/users/{id}`               | Обновить пользователя           | Admin  |
| DELETE| `/users/{id}`               | Удалить пользователя            | Admin  |
| GET   | `/users/{id}/accounts`      | Счета пользователя              | Admin  |
| POST  | `/users/{id}/accounts`      | Создать счёт пользователю       | Admin  |
| GET   | `/accounts/{id}`            | Любой счёт по ID                | Admin  |
| DELETE| `/accounts/{id}`            | Удалить любой счёт              | Admin  |

### Webhook (`/api/webhook`)

| Метод | Путь      | Описание                                       | Доступ    |
|-------|-----------|------------------------------------------------|-----------|
| POST  | `/payment`| Обработка платёжного вебхука | Публичный |

Формат подписи: `SHA256("{account_id}{amount}{transaction_id}{user_id}{PAYMENT_SECRET_KEY}")`

---

## Тесты

```bash
# Убедитесь, что .venv активировано и зависимости установлены
pytest -v
```

Тесты используют отдельную базу данных `test_bank_test`, которая создаётся и удаляется автоматически. Покрытие: 31 тест (auth, users, admin, webhook).

```bash
# Запуск только определённого модуля
pytest tests/test_auth.py -v
pytest tests/test_webhook.py -v
```

---

## Вебхук (тестирование через UI)

1. Откройте http://localhost:8000
2. Войдите как `user@test.com` / `userpass`
3. Перейдите на вкладку **Webhook**
4. Укажите User ID, Account ID, сумму
5. Нажмите **Сгенерировать** для Transaction ID
6. Секретный ключ предзаполнен (`gfdmhghif38yrf9ew0jkf32`), должен совпадать с `PAYMENT_SECRET_KEY` в `.env`
7. Нажмите **Отправить вебхук**

Подпись вычисляется на клиенте по формуле:
```
SHA256("{account_id}{amount}{transaction_id}{user_id}{secret_key}")
```
