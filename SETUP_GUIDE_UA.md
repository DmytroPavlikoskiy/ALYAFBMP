# 🗺️ Карта Місії — Запуск Marketplace MVP

> **Для кого цей гайд?** Для студентів, які хочуть запустити весь проєкт локально на своєму комп'ютері — без Docker, вручну, крок за кроком.
>
> **Чому так багато кроків?** Тому що наш проєкт — це **оркестр із 7 музикантів**. Кожен сервіс — окремий інструмент. Якщо хоч один мовчить — музики немає. Саме тому ми пізніше вивчимо Docker: він запускає весь оркестр **однією командою**. А поки — насолоджуйся процесом! 🎶

---

## Зміст

1. [🛠 Підготовка — що має бути встановлено](#1--підготовка--що-має-бути-встановлено)
2. [🗂 Структура проєкту](#2--структура-проєкту)
3. [📦 Крок 1 — База даних та Redis](#3--крок-1--база-даних-та-redis)
4. [🐍 Крок 2 — Backend (FastAPI)](#4--крок-2--backend-fastapi)
5. [⚙️ Крок 3 — Celery (черга завдань)](#5-️-крок-3--celery-черга-завдань)
6. [🤖 Крок 4 — Telegram Bot](#6--крок-4--telegram-bot)
7. [⚛️ Крок 5 — Frontend (React)](#7-️-крок-5--frontend-react)
8. [🔑 Довідник змінних середовища](#8--довідник-змінних-середовища)
9. [🔗 Як сервіси спілкуються між собою](#9--як-сервіси-спілкуються-між-собою)
10. [🚨 Типові помилки та їхнє вирішення](#10--типові-помилки-та-їхнє-вирішення)
11. [⏹ Як зупинити все](#11--як-зупинити-все)
12. [🎓 Підсумок — навіщо Docker?](#12--підсумок--навіщо-docker)

---

## 1. 🛠 Підготовка — що має бути встановлено

Перед тим як починати, переконайся, що на твоєму комп'ютері є все необхідне.  
Запусти кожну команду в терміналі та перевір версію:

| Інструмент | Мінімальна версія | Як перевірити |
|------------|------------------|---------------|
| **Python** | 3.10+ | `python --version` |
| **Node.js** | 18+ | `node --version` |
| **npm** | 9+ | `npm --version` |
| **PostgreSQL** | 14+ | `psql --version` |
| **Redis** | 6+ | `redis-server --version` |
| **Git** | будь-яка | `git --version` |

### Як встановити те, чого не вистачає

**macOS (через Homebrew)**
```bash
brew install python@3.11 node postgresql redis
```

**Windows**
- **Python:** https://www.python.org/downloads/ *(не забудь поставити галочку "Add to PATH"!)*
- **Node.js:** https://nodejs.org/
- **PostgreSQL:** https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- **Redis:** https://github.com/microsoftarchive/redis/releases *(або використовуй WSL2)*

**Ubuntu / Debian**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv nodejs npm postgresql redis-server
```

> ✅ **Перевір себе:** Запусти всі п'ять команд перевірки зверху. Якщо кожна повертає номер версії — ти готовий рухатися далі!

---

## 2. 🗂 Структура проєкту

Перед запуском добре розуміти, де що лежить:

```
ALYAFBMP/                    ← корінь проєкту
├── backend/                 ← весь Python-код
│   ├── apps/
│   │   ├── auth/            ← реєстрація та логін
│   │   ├── products/        ← товари та фото
│   │   ├── orders/          ← замовлення
│   │   ├── users/           ← профілі користувачів
│   │   ├── chats/           ← повідомлення
│   │   ├── communication/   ← WebSocket (реал-тайм)
│   │   ├── moderation/      ← перевірка оголошень
│   │   ├── celery/          ← фонові завдання
│   │   └── bot/             ← Telegram-бот
│   ├── common/              ← спільні моделі, БД, залежності
│   ├── main.py              ← точка входу FastAPI
│   ├── config.py            ← усі налаштування з .env
│   └── migrations/          ← Alembic: схема БД
├── frontend/                ← React + Vite (інтерфейс)
└── requirements.txt         ← список Python-пакетів
```

---

## 3. 📦 Крок 1 — База даних та Redis

> 🎻 **Аналогія з оркестром:** PostgreSQL і Redis — це **сцена та пульт звукорежисера**. Усі інші музиканти виходять на сцену лише після того, як вона готова.

### 🐘 PostgreSQL

**macOS**
```bash
brew services start postgresql@14
```

**Windows** *(від імені адміністратора)*
```powershell
net start postgresql-x64-14
```

**Ubuntu / Debian**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql   # щоб запускалось автоматично після перезавантаження
```

---

### Створи базу даних та користувача

Відкрий PostgreSQL-консоль:
```bash
# macOS / Linux
psql -U postgres

# Windows: відкрий psql з меню Пуск або знайди pgAdmin
```

Виконай ці SQL-команди всередині `psql`:

```sql
CREATE DATABASE marketplace;
CREATE USER marketplace_user WITH PASSWORD 'strongpassword';
GRANT ALL PRIVILEGES ON DATABASE marketplace TO marketplace_user;
\q
```

> 💡 **Підказка:** Якщо хочеш використати стандартний `postgres`/`1111` — просто переконайся, що PostgreSQL дозволяє вхід із паролем. Тоді можна не створювати окремого користувача.

---

### 🔴 Redis

**macOS**
```bash
brew services start redis

# Перевір, що Redis відповідає:
redis-cli ping
# Має повернути: PONG
```

**Windows**
```powershell
net start Redis
# або просто запусти redis-server.exe
```

**Ubuntu / Debian**
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Перевір:
redis-cli ping
```

> ✅ **Результат цього кроку:** PostgreSQL і Redis запущені. Переходимо до Python!

---

## 4. 🐍 Крок 2 — Backend (FastAPI)

> 🎻 **Аналогія з оркестром:** FastAPI — це **диригент**. Він приймає запити від фронтенду та бота, керує базою даних, і роздає завдання Celery.

> 🖥️ **Відкрий новий термінал.** Назви його для себе `[BACKEND]`.

### Крок 2.1 — Створи та активуй віртуальне середовище

```bash
# Перейди в корінь проєкту
cd /шлях/до/ALYAFBMP

# Створи venv (виконується один раз)
python -m venv venv

# Активуй його:
# macOS / Linux:
source venv/bin/activate

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (CMD):
venv\Scripts\activate.bat
```

**Як зрозуміти, що venv активований?**  
На початку рядка терміналу з'явиться `(venv)` — наприклад:
```
(venv) maksim@MacBook ALYAFBMP %
```

> ⚠️ **Важливо:** Вирутальне середовище потрібно **активувати в кожному новому терміналі**, де ти запускаєш Python-код. Без цього Python не знайде встановлені пакети.

### Крок 2.2 — Встанови Python-пакети

```bash
pip install -r requirements.txt
```

Це встановить FastAPI, SQLAlchemy, Celery, aiogram та ще ~30 бібліотек.  
**Першого разу займе 1–3 хвилини** — це нормально, чекай.

### Крок 2.3 — Налаштуй файл `.env`

Скопіюй шаблон:
```bash
cp backend/.env.example backend/.env
```

Відкрий `backend/.env` у текстовому редакторі та заповни:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:1111@127.0.0.1:5432/marketplace
REDIS_URL=redis://127.0.0.1:6379/0
JWT_SECRET=замінити-на-довгий-випадковий-рядок
BOT_SECRET=ще-один-секрет
BOT_TOKEN=токен-твого-telegram-бота
ADMIN_ID=твій-telegram-числовий-id
```

Згенеруй надійний секрет для `JWT_SECRET`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Крок 2.4 — Застосуй міграції бази даних *(виконується один раз)*

```bash
cd backend
alembic upgrade head
```

Ця команда створює всі таблиці в PostgreSQL: `users`, `products`, `orders`, `chats` тощо.

> 💡 **Що таке міграція?** Це скрипт, який змінює структуру бази даних. Alembic відстежує зміни в моделях і автоматично створює SQL для оновлення схеми.

### Крок 2.5 — Запусти сервер

```bash
cd backend   # якщо ще не в цій папці
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

| Прапор | Що робить |
|--------|-----------|
| `--host 0.0.0.0` | Приймає підключення з будь-якого інтерфейсу |
| `--port 8000` | Слухає на порту 8000 |
| `--reload` | Перезапускається автоматично при зміні файлів *(лише для розробки)* |

**Якщо все добре, ти побачиш:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

> 🎉 **Backend запущений!**
> - API: http://localhost:8000
> - Інтерактивна документація: http://localhost:8000/docs
> - Адмін-панель: http://localhost:8000/admin

---

## 5. ⚙️ Крок 3 — Celery (черга завдань)

> 🎻 **Аналогія з оркестром:** Celery — це **перкусіоністи**. Вони не грають постійно, але коли приходить їхній час — ударяють точно та потужно. Worker виконує завдання, Beat — задає ритм (розклад).

> 🚨 **ВАЖЛИВО:** Для Celery потрібно відкрити **два окремих термінали** — один для Worker, один для Beat. Вони — різні процеси!

---

### Термінал A: Celery Worker

> 🖥️ **Відкрий новий термінал.** Назви його `[CELERY WORKER]`.

```bash
# 1. Активуй venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate.bat       # Windows

# 2. Перейди в папку backend
cd backend

# 3. Запусти Worker
celery -A apps.celery.celery_app.celery_app worker --loglevel=info
```

**Якщо ти на Windows і виникає помилка — додай `-P eventlet`:**
```bash
celery -A apps.celery.celery_app.celery_app worker --loglevel=info -P eventlet
```

**Що робить Worker?**
- Отримує сповіщення від FastAPI: *"є нове замовлення — надішли повідомлення продавцю"*
- Виконує це завдання у фоні, не блокуючи основний сервер

**Якщо Worker запустився успішно, побачиш:**
```
[tasks]
  . apps.celery.celery_app.clear_expired_bans
  . apps.celery.celery_app.notify_seller_new_order

[2024-...] INFO/MainProcess celery@hostname ready.
```

---

### Термінал Б: Celery Beat

> 🖥️ **Відкрий ЩЕ ОДИН новий термінал.** Назви його `[CELERY BEAT]`.

```bash
# 1. Активуй venv
source venv/bin/activate

# 2. Перейди в папку backend
cd backend

# 3. Запусти Beat
celery -A apps.celery.celery_app.celery_app beat --loglevel=info
```

**Що робить Beat?**

| Завдання | Коли запускається | Для чого |
|----------|------------------|----------|
| `clear_expired_bans` | Щодня опівночі | Знімає бан з користувачів, у яких закінчився строк блокування |

> 💡 **Аналогія:** Beat — це будильник. Він каже Worker-у: *"Час прибрати старі бани!"* Але виконує роботу саме Worker. Обидва мають бути запущені.

> ✅ **Результат цього кроку:** Два нових термінали з Celery Worker і Beat.

---

## 6. 🤖 Крок 4 — Telegram Bot

> 🎻 **Аналогія з оркестром:** Бот — це **посланець між глядачами та сценою**. Він спілкується з Telegram-хмарою та передає команди модерації до нашого API.

> 🖥️ **Відкрий новий термінал.** Назви його `[BOT]`.

### Крок 4.1 — Отримай токен бота

1. Відкрий Telegram і напиши боту [@BotFather](https://t.me/BotFather)
2. Відправ команду `/newbot`
3. Дай боту ім'я та username (наприклад, `MyMarketplaceBot`)
4. Скопіюй токен — він виглядає так: `123456789:ABCdef...`

### Крок 4.2 — Дізнайся свій Telegram ID

1. Напиши боту [@userinfobot](https://t.me/userinfobot)
2. Він відповість твоїм числовим ID, наприклад: `123456789`
3. Цей ID вкажи як `ADMIN_ID` — він отримуватиме картки модерації

### Крок 4.3 — Додай дані в `.env`

Відкрий `backend/.env` та переконайся, що є ці рядки:

```dotenv
BOT_TOKEN=123456789:ABCdef...          # Токен від BotFather
ADMIN_ID=123456789                     # Твій Telegram ID (числовий)
BOT_SECRET=той-самий-секрет-що-в-api  # Має збігатися з BOT_SECRET
API_BASE_URL=http://127.0.0.1:8000    # Адреса FastAPI
```

> ⚠️ **`BOT_SECRET` має бути однаковим** і в `.env`, і в налаштуваннях API. Бот використовує його для автентифікації при зверненні до внутрішніх ендпоінтів.

### Крок 4.4 — Запусти бота

```bash
# 1. Активуй venv
source venv/bin/activate

# 2. Перейди в папку backend
cd backend

# 3. Запусти бота
python -m apps.bot.bot
```

**Якщо все правильно:**
```
INFO - Bot started
INFO - Listening to Redis moderation_channel...
```

**Що вміє бот?**
- 📋 **Модерація:** Отримує картку нового оголошення в Telegram і дає кнопки ✅ Схвалити / ❌ Відхилити
- 🛒 **Магазин:** Клієнти можуть переглядати товари, обране, логінитись — прямо в Telegram

> ⚠️ **Бот вимагає, щоб FastAPI вже працював** — він звертається до нього через HTTP для всіх дій.

---

## 7. ⚛️ Крок 5 — Frontend (React)

> 🎻 **Аналогія з оркестром:** React — це **сцена, яку бачить публіка**. Усі інші сервіси — за куліса́ми.

> 🖥️ **Відкрий новий термінал.** Назви його `[FRONTEND]`.  
> *(Цей термінал не потребує Python чи venv — тільки Node.js)*

### Крок 5.1 — Перейди в папку frontend

```bash
cd frontend
```

### Крок 5.2 — Встанови залежності *(один раз)*

```bash
npm install
```

Це завантажує React, Axios, Tailwind CSS, Lucide та інші бібліотеки в папку `node_modules`.

### Крок 5.3 — Запусти dev-сервер

```bash
npm run dev
```

**Якщо все добре, побачиш:**
```
  VITE v8.x.x  ready in 300ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

> 🎉 **Фронтенд запущений на http://localhost:5173**

### Що можна робити у браузері?

| Сторінка | URL | Що робить |
|----------|-----|-----------|
| Стрічка товарів | `/` | Перегляд оголошень, пошук, фільтри |
| Вхід | `/login` | Авторизація |
| Реєстрація | `/register` | Новий акаунт |
| Товар | `/products/:id` | Деталі, купити, написати продавцю |
| Нове оголошення | `/create` | Форма для продавця |
| Профіль | `/profile` | Мої оголошення, замовлення, сповіщення |
| Чати | `/chats` | Список переписок |

---

## 8. 🔑 Довідник змінних середовища

Усі налаштування бекенду — у файлі `backend/.env`.  
**Ніколи не додавай цей файл у Git!** (він вже є в `.gitignore`)

```dotenv
# ── Загальне ──────────────────────────────────────────────────────────────────
PROJECT_NAME=Marketplace MVP
DEBUG=false              # true — більше логів SQL (для розробки)

# ── PostgreSQL ────────────────────────────────────────────────────────────────
# Формат: postgresql+asyncpg://КОРИСТУВАЧ:ПАРОЛЬ@ХОСТ:ПОРТ/БАЗА
DATABASE_URL=postgresql+asyncpg://postgres:1111@127.0.0.1:5432/marketplace

# ── Redis ─────────────────────────────────────────────────────────────────────
# Формат: redis://ХОСТ:ПОРТ/НОМЕР_БД
REDIS_URL=redis://127.0.0.1:6379/0

# ── JWT (автентифікація) ──────────────────────────────────────────────────────
JWT_SECRET=замінити-на-32-символи-випадкового-тексту
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── Telegram Bot ──────────────────────────────────────────────────────────────
BOT_TOKEN=токен-від-botfather
ADMIN_ID=твій-числовий-telegram-id
BOT_SECRET=спільний-секрет-між-ботом-та-api
API_BASE_URL=http://127.0.0.1:8000

# ── CORS (дозволені origin для браузера) ──────────────────────────────────────
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## 9. 🔗 Як сервіси спілкуються між собою

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Твій комп'ютер                                 │
│                                                                         │
│  ┌────────────┐  HTTP/WS  ┌──────────────────────────────────────────┐ │
│  │  Браузер   │◄─────────►│  React (Vite)         :5173              │ │
│  └────────────┘           └──────────────────────────────────────────┘ │
│                                       │  REST + WebSocket              │
│                                       ▼                                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                   FastAPI  :8000                                   │ │
│  │     /api/v1/*     /ws/chat/*     /admin     /docs                  │ │
│  └──────────────────┬──────────────────────────┬──────────────────── ┘ │
│                     │ SQL (asyncpg)             │ Redis pub/sub + tasks │
│                     ▼                           ▼                       │
│  ┌──────────────────────────┐   ┌──────────────────────────────────┐   │
│  │  PostgreSQL       :5432  │   │  Redis                  :6379    │   │
│  └──────────────────────────┘   └───────────────┬──────────────────┘   │
│                                                  │ Celery broker        │
│                                    ┌─────────────┴───────────┐         │
│                                    │                         │          │
│                           ┌────────┴──────┐       ┌──────────┴────┐    │
│                           │ Celery Worker │       │  Celery Beat  │    │
│                           │ (виконує)     │       │  (планує)     │    │
│                           └───────────────┘       └───────────────┘    │
│                                                                         │
│  ┌──────────────────────────────────────────────┐                       │
│  │  Telegram Bot (python -m apps.bot.bot)       │──► Telegram (хмара)  │
│  │  Читає Redis moderation_channel              │◄── HTTP → FastAPI    │
│  └──────────────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### Порядок запуску — це ОБОВ'ЯЗКОВО

Запускай сервіси саме в цьому порядку:

```
1️⃣  PostgreSQL      (база даних має існувати до міграцій)
2️⃣  Redis           (брокер має бути готовий до Celery та бота)
3️⃣  FastAPI         (спочатку: alembic upgrade head)
4️⃣  Celery Worker   (потрібен Redis і спільний код із FastAPI)
5️⃣  Celery Beat     (потрібен Worker для виконання завдань)
6️⃣  Telegram Bot    (потрібен FastAPI для HTTP-запитів)
7️⃣  React           (можна запускати в будь-який час, але дані є лише якщо FastAPI працює)
```

---

## 10. 🚨 Типові помилки та їхнє вирішення

### ❌ `connection refused` на порті 5432
**Проблема:** PostgreSQL не запущений.
```bash
brew services start postgresql@14   # macOS
sudo systemctl start postgresql     # Linux
```

---

### ❌ `connection refused` на порті 6379
**Проблема:** Redis не запущений.
```bash
brew services start redis     # macOS
sudo systemctl start redis    # Linux
redis-server                  # або запусти вручну
```

---

### ❌ `ModuleNotFoundError: No module named 'fastapi'`
**Проблема:** Віртуальне середовище не активоване.
```bash
source venv/bin/activate    # macOS / Linux
venv\Scripts\activate.bat   # Windows
```

---

### ❌ Помилка при `alembic upgrade head`
**Проблема:** База даних не існує або неправильний `DATABASE_URL`.
1. Перевір, що PostgreSQL запущений
2. Перевір `DATABASE_URL` у `backend/.env`
3. Переконайся, що база `marketplace` створена (`CREATE DATABASE marketplace;`)

---

### ❌ `[Errno 48] Address already in use` на порті 8000
**Проблема:** Щось інше вже займає порт 8000.
```bash
# Знайди і зупини процес (macOS / Linux):
lsof -i :8000
kill -9 <PID>

# Або запусти на іншому порту:
uvicorn main:app --port 8001
```

---

### ❌ Celery: `Cannot connect to redis://...`
**Проблема:** Redis не запущений. Запусти Redis спочатку (Крок 1).

---

### ❌ React показує `Network Error` або порожню стрічку
**Проблема:** FastAPI не запущений або CORS не налаштований.
1. Переконайся, що FastAPI запущений на порту 8000
2. Перевір `CORS_ORIGINS` у `backend/.env` — там має бути `http://localhost:5173`

---

### ❌ Celery зависає на Windows
**Вирішення:** Використай eventlet-пул:
```bash
celery -A apps.celery.celery_app.celery_app worker --loglevel=info -P eventlet
```

---

### ❌ Бот не реагує на кнопки модерації
**Причин може бути декілька:**
- `BOT_SECRET` у `.env` не збігається з тим, що очікує API
- FastAPI не запущений
- `ADMIN_ID` неправильний

---

## 11. ⏹ Як зупинити все

У кожному терміналі натисни **`Ctrl + C`** — це зупинить процес.

Щоб зупинити фонові сервіси:

**macOS**
```bash
brew services stop postgresql@14
brew services stop redis
```

**Linux**
```bash
sudo systemctl stop postgresql
sudo systemctl stop redis-server
```

**Деактивуй venv:**
```bash
deactivate
```

---

## 12. 🎓 Підсумок — навіщо Docker?

Ти щойно запустив **7 окремих процесів** у 7 різних терміналах.  
Ти вручну керував:

- ❌ Порядком запуску сервісів
- ❌ Правильними командами для своєї ОС
- ❌ Активацією venv у кожному терміналі
- ❌ Конфліктами портів
- ❌ Змінними середовища в декількох місцях
- ❌ Ручним створенням бази даних

**А тепер уяви, що всі твої одногрупники теж хочуть запустити проєкт на своїх комп'ютерах. У кожного — своя ОС, свій Python, свій PostgreSQL...**

**Docker вирішує все це однією командою:**
```bash
docker compose up --build
```

Усі 7 сервісів запускаються в правильному порядку, в ізольованому середовищі, з однаковими налаштуваннями — незалежно від ОС. Без жодного `brew install`, `apt install` чи `net start`.

> 🚀 **Наступний урок — Docker Compose. Ти вже знаєш, що саме він автоматизує. Тепер побачиш, як він це робить.**

---

*Останнє оновлення: квітень 2026 | Marketplace MVP v1*
