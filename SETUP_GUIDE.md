# 🛠️ Local Setup Guide — Marketplace MVP

> **Goal of this document:** show you exactly how to start every piece of the project *by hand*, in separate terminals, without Docker.  
> By the end you will have **7 processes** running simultaneously. This is why we will learn Docker next.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Structure Overview](#2-project-structure-overview)
3. [Service 1 — PostgreSQL](#3-service-1--postgresql)
4. [Service 2 — Redis](#4-service-2--redis)
5. [Service 3 — FastAPI Backend](#5-service-3--fastapi-backend)
6. [Service 4 — Celery Worker](#6-service-4--celery-worker)
7. [Service 5 — Celery Beat (Scheduler)](#7-service-5--celery-beat-scheduler)
8. [Service 6 — Telegram Bot](#8-service-6--telegram-bot)
9. [Service 7 — React Frontend](#9-service-7--react-frontend)
10. [Environment Variables Reference](#10-environment-variables-reference)
11. [How Services Connect](#11-how-services-connect)
12. [Common Errors & Fixes](#12-common-errors--fixes)
13. [Stopping Everything](#13-stopping-everything)

---

## 1. Prerequisites

Install these tools **before** starting. Check each one with the version command shown.

| Tool | Minimum version | How to check |
|------|----------------|-------------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| PostgreSQL | 14+ | `psql --version` |
| Redis | 6+ | `redis-server --version` |
| Git | any | `git --version` |

### Installing missing tools

**macOS (Homebrew)**
```bash
brew install python@3.11 node postgresql redis
```

**Windows**
- Python: https://www.python.org/downloads/ (check "Add to PATH")
- Node.js: https://nodejs.org/
- PostgreSQL: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- Redis: https://github.com/microsoftarchive/redis/releases (or use WSL2)

**Ubuntu / Debian**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv nodejs npm postgresql redis-server
```

---

## 2. Project Structure Overview

```
ALYAFBMP/                   ← project root
├── backend/                ← FastAPI + Celery + Bot
│   ├── apps/
│   │   ├── auth/
│   │   ├── products/
│   │   ├── orders/
│   │   ├── users/
│   │   ├── chats/
│   │   ├── communication/
│   │   ├── moderation/
│   │   ├── celery/         ← Celery app & tasks
│   │   └── bot/            ← Telegram bot
│   ├── common/             ← Shared models, DB, deps
│   ├── main.py             ← FastAPI entry point
│   ├── config.py           ← All env-var settings
│   └── migrations/         ← Alembic DB migrations
├── frontend/               ← React (Vite) SPA
└── requirements.txt        ← Python dependencies
```

---

## 3. Service 1 — PostgreSQL

PostgreSQL is the main database. It must be running **before** the backend starts.

### macOS

```bash
# Start (if installed via Homebrew)
brew services start postgresql@14

# OR start manually
pg_ctl -D /usr/local/var/postgresql@14 start
```

### Windows

```powershell
# Start via Services panel: Win+R → services.msc → find "postgresql-x64-14" → Start
# OR via command line (run as Administrator):
net start postgresql-x64-14
```

### Ubuntu / Debian

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql   # auto-start on boot
```

---

### Create the database and user

Open the PostgreSQL interactive shell:

```bash
# macOS / Linux
psql -U postgres

# Windows (from PostgreSQL bin folder, e.g. C:\Program Files\PostgreSQL\14\bin)
psql -U postgres
```

Then run these SQL commands inside `psql`:

```sql
CREATE DATABASE marketplace;
CREATE USER marketplace_user WITH PASSWORD 'strongpassword';
GRANT ALL PRIVILEGES ON DATABASE marketplace TO marketplace_user;
\q
```

> **Tip:** You can use the default `postgres` user with password `1111` to match the project's default `DATABASE_URL` — just make sure PostgreSQL allows password authentication.

---

### Run database migrations

After the backend virtual environment is set up (step 5), run:

```bash
# From the backend/ directory
cd backend
alembic upgrade head
```

This creates all tables (users, products, orders, chats, etc.).

---

## 4. Service 2 — Redis

Redis is used for:
- **Celery broker** — queues background tasks
- **Pub/Sub** — real-time chat fan-out and moderation messages
- **Bot token cache** — stores Telegram JWT tokens

### macOS

```bash
brew services start redis

# Test it's working:
redis-cli ping
# Should print: PONG
```

### Windows

```powershell
# If installed as a service:
net start Redis

# OR run directly:
redis-server
```

### Ubuntu / Debian

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test:
redis-cli ping
```

> Redis runs on **port 6379** by default. No further configuration needed for development.

---

## 5. Service 3 — FastAPI Backend

> **Open a new terminal window** for this service. Label it `[BACKEND]`.

### Step 1 — Create and activate a virtual environment

```bash
# Navigate to the project root
cd /path/to/ALYAFBMP

# Create virtual environment (do this once)
python -m venv venv

# Activate it
# macOS / Linux:
source venv/bin/activate

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (CMD):
venv\Scripts\activate.bat
```

You should see `(venv)` at the start of your prompt.

### Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

> This installs FastAPI, SQLAlchemy, Celery, aiogram, and all other packages.  
> Takes 1–3 minutes on first run.

### Step 3 — Create the `.env` file

Copy the example and fill in your values:

```bash
# From the project root
cp backend/.env.example backend/.env
```

Open `backend/.env` and set at minimum:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:1111@127.0.0.1:5432/marketplace
REDIS_URL=redis://127.0.0.1:6379/0
JWT_SECRET=replace-with-a-long-random-secret
BOT_SECRET=replace-with-another-secret
BOT_TOKEN=your-telegram-bot-token-here
ADMIN_ID=your-telegram-user-id
```

> Generate a strong secret: `python -c "import secrets; print(secrets.token_hex(32))"`

### Step 4 — Run Alembic migrations

```bash
cd backend
alembic upgrade head
cd ..
```

### Step 5 — Start the server

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

| Flag | Meaning |
|------|---------|
| `--host 0.0.0.0` | Accept connections from any network interface |
| `--port 8000` | Listen on port 8000 |
| `--reload` | Auto-restart when you edit a file (development only) |

✅ **Backend is running at:** http://localhost:8000  
✅ **Interactive API docs at:** http://localhost:8000/docs  
✅ **Admin panel at:** http://localhost:8000/admin

---

## 6. Service 4 — Celery Worker

> **Open a NEW terminal window.** Label it `[CELERY WORKER]`.  
> The virtual environment must be activated in this terminal too.

```bash
# Activate venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate.bat       # Windows

# Navigate to the backend directory (IMPORTANT — Celery needs this as working dir)
cd backend

# Start the worker
celery -A apps.celery.celery_app.celery_app worker --loglevel=info
```

**Windows users:** Add `-P eventlet` if you encounter errors:

```bash
celery -A apps.celery.celery_app.celery_app worker --loglevel=info -P eventlet
```

### What this worker does

- Sends **seller notifications** when a new order is placed
- Executes any other async tasks queued by FastAPI

You will see output like:
```
[tasks]
  . apps.celery.celery_app.clear_expired_bans
  . apps.celery.celery_app.notify_seller_new_order
[2024-...] INFO/MainProcess celery@hostname ready.
```

---

## 7. Service 5 — Celery Beat (Scheduler)

> **Open a NEW terminal window.** Label it `[CELERY BEAT]`.

Celery Beat is the clock that triggers scheduled tasks on a timer (like a cron job).

```bash
# Activate venv
source venv/bin/activate

# Navigate to the backend directory
cd backend

# Start the scheduler
celery -A apps.celery.celery_app.celery_app beat --loglevel=info
```

### What Beat schedules

| Task | Schedule | Purpose |
|------|----------|---------|
| `clear_expired_bans` | Every midnight | Unban users whose ban period has expired |

> ⚠️ **Beat and Worker are separate processes.** Beat only *schedules* tasks; the Worker *executes* them. Both must be running for scheduled jobs to work.

---

## 8. Service 6 — Telegram Bot

> **Open a NEW terminal window.** Label it `[BOT]`.

The bot handles:
- Moderation approvals (approve/reject products from Telegram)
- Customer interactions (browsing shop, favorites, login via Telegram)

### Step 1 — Get a Bot Token

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the token (looks like `123456789:ABCdef...`)

### Step 2 — Get your Telegram Admin ID

1. Message [@userinfobot](https://t.me/userinfobot)
2. It will reply with your numeric ID (e.g. `123456789`)

### Step 3 — Set environment variables

Make sure `backend/.env` has:

```dotenv
BOT_TOKEN=123456789:ABCdef...          # From BotFather
ADMIN_ID=123456789                     # Your Telegram user ID
BOT_SECRET=same-secret-as-in-backend  # Must match BOT_SECRET in .env
API_BASE_URL=http://127.0.0.1:8000    # Where the FastAPI server is running
```

### Step 4 — Start the bot

```bash
# Activate venv
source venv/bin/activate

# Run from the backend directory
cd backend
python -m apps.bot.bot
```

You should see:
```
INFO - Bot started
INFO - Listening to Redis moderation_channel...
```

> **Note:** The bot communicates with the backend via HTTP (not direct DB access). The FastAPI server **must be running** before you start the bot.

---

## 9. Service 7 — React Frontend

> **Open a NEW terminal window.** Label it `[FRONTEND]`.  
> This terminal needs **Node.js**, not Python.

### Step 1 — Install dependencies (first time only)

```bash
cd frontend
npm install
```

### Step 2 — Start the development server

```bash
npm run dev
```

✅ **Frontend is running at:** http://localhost:5173

### How the frontend connects to the backend

The API base URL is set in `frontend/src/api/axios.js`:

```js
baseURL: 'http://localhost:8000/api/v1'
```

If your backend runs on a different port, update this value.

### Step 3 — Build for production (optional)

```bash
npm run build
```

This creates an optimized bundle in `frontend/dist/`.

---

## 10. Environment Variables Reference

All backend settings live in `backend/.env`. Here is every variable:

```dotenv
# ── General ──────────────────────────────────────────────────────────────────
PROJECT_NAME=Marketplace MVP
DEBUG=false                          # Set to true for verbose SQL logs

# ── PostgreSQL ────────────────────────────────────────────────────────────────
# Format: postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
DATABASE_URL=postgresql+asyncpg://postgres:1111@127.0.0.1:5432/marketplace

# ── Redis ─────────────────────────────────────────────────────────────────────
# Format: redis://HOST:PORT/DB_NUMBER
REDIS_URL=redis://127.0.0.1:6379/0

# ── JWT Authentication ────────────────────────────────────────────────────────
JWT_SECRET=replace-with-32-plus-random-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── Telegram Bot ──────────────────────────────────────────────────────────────
BOT_TOKEN=your-token-from-botfather
ADMIN_ID=your-telegram-numeric-id
BOT_SECRET=shared-secret-between-bot-and-api
API_BASE_URL=http://127.0.0.1:8000

# ── CORS (comma-separated origins, or * for dev) ──────────────────────────────
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

> 🔐 **Never commit `.env` to Git.** The `.gitignore` should already exclude it. Double-check with `git status`.

---

## 11. How Services Connect

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Your Computer                               │
│                                                                     │
│  ┌──────────┐  HTTP    ┌──────────────────────────────────────┐    │
│  │ Browser  │◄────────►│  React (Vite)  :5173                 │    │
│  └──────────┘          └──────────────────────────────────────┘    │
│                                    │ REST + WebSocket               │
│                                    ▼                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │               FastAPI  :8000                                  │  │
│  │  /api/v1/*   /ws/chat/*   /admin   /docs                      │  │
│  └───────────────┬──────────────────────┬─────────────────────  ┘  │
│                  │ SQL (asyncpg)         │ Redis pub/sub + tasks     │
│                  ▼                       ▼                           │
│  ┌────────────────────┐   ┌─────────────────────────────────────┐   │
│  │  PostgreSQL  :5432 │   │  Redis  :6379                       │   │
│  └────────────────────┘   └──────────────┬──────────────────────┘   │
│                                          │ Celery broker/backend     │
│                            ┌─────────────┴──────────────┐           │
│                            │                            │            │
│                   ┌────────┴───────┐        ┌──────────┴──────┐     │
│                   │ Celery Worker  │        │  Celery Beat    │     │
│                   │ (executes jobs)│        │  (schedules)    │     │
│                   └────────────────┘        └─────────────────┘     │
│                                                                     │
│  ┌──────────────────────────────────────┐                           │
│  │  Telegram Bot  (python -m apps.bot)  │──► Telegram API (cloud)  │
│  │  Reads Redis moderation_channel      │◄── HTTP → FastAPI :8000  │
│  └──────────────────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

**Startup order matters:**

```
1. PostgreSQL   (database must exist before migrations)
2. Redis        (broker must be up before Celery/Bot)
3. FastAPI      (run migrations first: alembic upgrade head)
4. Celery Worker
5. Celery Beat
6. Telegram Bot (needs FastAPI running to make HTTP calls)
7. React        (can start at any time, but needs FastAPI for data)
```

---

## 12. Common Errors & Fixes

### ❌ `connection refused` on port 5432
PostgreSQL is not running.
```bash
brew services start postgresql@14    # macOS
sudo systemctl start postgresql      # Linux
```

### ❌ `connection refused` on port 6379
Redis is not running.
```bash
brew services start redis      # macOS
sudo systemctl start redis     # Linux
redis-server                   # start manually
```

### ❌ `ModuleNotFoundError: No module named 'fastapi'`
Virtual environment is not activated.
```bash
source venv/bin/activate    # macOS / Linux
venv\Scripts\activate.bat   # Windows
```

### ❌ `alembic.util.exc.CommandError: Target database is not up to date`
Run the migration:
```bash
cd backend && alembic upgrade head
```

### ❌ `INVALID_CREDENTIALS` when logging in via the bot
The `BOT_SECRET` in `.env` does not match `X-Bot-Secret` header the bot sends.  
Make sure both the bot and API read from the same `.env` file.

### ❌ `[Errno 48] Address already in use` (port 8000)
Another process is using port 8000.
```bash
# Find and kill the process:
lsof -i :8000           # macOS / Linux
kill -9 <PID>

# Or change port:
uvicorn main:app --port 8001
```

### ❌ Celery `[ERROR] consumer: Cannot connect to redis://...`
Redis is not running. Start it first (see step 4).

### ❌ React shows `Network Error` or blank feed
The backend is not running, or CORS is blocking the request.  
Check that `CORS_ORIGINS` in `.env` includes `http://localhost:5173`.

### ❌ Celery worker hangs on Windows
Use the eventlet pool:
```bash
celery -A apps.celery.celery_app.celery_app worker --loglevel=info -P eventlet
```

---

## 13. Stopping Everything

Press `Ctrl + C` in each terminal window to stop each service.

To stop background services (macOS):
```bash
brew services stop postgresql@14
brew services stop redis
```

To stop background services (Linux):
```bash
sudo systemctl stop postgresql
sudo systemctl stop redis-server
```

To deactivate the Python virtual environment:
```bash
deactivate
```

---

## 🎓 Reflection — Why Docker?

You just started **7 separate processes** across 7 terminal windows, manually managing:

- Installation order dependencies
- Port conflicts
- Environment variables in multiple places
- OS-specific commands (macOS vs Windows vs Linux)
- Manual database creation

**Docker solves all of this with one command:**
```bash
docker compose up --build
```

That's it. All 7 services start in the correct order, isolated from your OS, with shared environment variables and automatic networking. Next lesson — we'll do exactly that.

---

*Last updated: April 2026 | Marketplace MVP v1*
