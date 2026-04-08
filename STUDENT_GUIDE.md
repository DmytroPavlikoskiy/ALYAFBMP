# STUDENT_GUIDE — дорожня карта «в коді»

Цей документ доповнює [API-contract.md](API-contract.md). **Джерело правди для шляхів API** — контракт; тут — де саме писати логіку та як запускати скелет.

## Конфігурація (.env)

Файли `.env` та `.env_dev` у каталозі `backend/` (див. `Settings` у `backend/config.py`):

- `DATABASE_URL` — `postgresql+asyncpg://...`
- `REDIS_URL` — Redis для API та Celery
- `BOT_TOKEN` (або `TG_BOT_TOKEN`) — токен Telegram-бота
- `API_BASE_URL` — базовий URL FastAPI для httpx у боті (наприклад `http://127.0.0.1:8000`)
- `ADMIN_ID` — числовий Telegram user id адміністратора для модерації
- `DEBUG` — `true`/`false`
- Додатково: `JWT_SECRET`, `BOT_SECRET`, `CORS_ORIGINS` (через кому або `*`)

## Як запускати скелет

- З каталогу `backend/`: `uvicorn main:app --reload`
- Health без БД: `GET http://127.0.0.1:8000/health`
- Усі ендпоінти контракту під префіксом `/api/v1` (підключення в `backend/main.py`: auth, users, products, orders, moderation, communication).
- Веб-адмінка БД (SQLAdmin): `http://127.0.0.1:8000/admin` — див. [backend/apps/admin/admin_panel.py](backend/apps/admin/admin_panel.py).
- Статичні файли товарів плануйте зберігати в `backend/static/products/` (див. docstring у `backend/apps/products/router.py`, функція `create_product`).
- Celery (з `backend/`):  
  `celery -A apps.celery.celery_app.celery_app worker --loglevel=info`  
  `celery -A apps.celery.celery_app.celery_app beat --loglevel=info`
- Telegram-бот (окремо від API, лише httpx до REST; **без** імпорту БД у коді бота): `python3 -m apps.bot.bot` з каталогу `backend/`.

## Де що лежить (ORM)

- Усі таблиці описані в одному місці: [backend/common/models.py](backend/common/models.py) (SQLAlchemy 2.0, `Mapped`, async-сесії).
- Старі імпорти `apps.users.models` / `apps.products.models` реекспортують ті самі класи для зворотної сумісності.

## Розподіл по групах (з API-contract.md)

Нижче — **які файли заповнювати**, щоб закрити завдання груп. Більшість ендпоінтів зараз повертає **501** або порожні дані; docstrings у функціях — покроковий псевдокод **українською**.

### Група 1 (Auth & User Security)

- **Файли:** [backend/apps/auth/router.py](backend/apps/auth/router.py), [backend/apps/auth/schemas.py](backend/apps/auth/schemas.py), [backend/common/deps.py](backend/common/deps.py) (`get_current_user_id`, JWT).
- **Контекст:** без цього не працюватимуть захищені маршрути (`/users/me`, створення товару тощо).

### Група 2 (Category Picker & Profile)

- **Файли:** [backend/apps/products/router.py](backend/apps/products/router.py) (функція `list_categories`), [backend/apps/users/router.py](backend/apps/users/router.py) (`read_me`, `save_preferences`).
- **Моделі:** `Category`, `UserPreference` у [backend/common/models.py](backend/common/models.py).

### Група 3 (Smart Feed & Search)

- **Файли:** [backend/apps/products/services/feed.py](backend/apps/products/services/feed.py), [backend/apps/products/router.py](backend/apps/products/router.py) (`product_detail`, за потреби уточнення `product_feed`).
- **Застарілий імпорт:** [backend/apps/products/services/feed_logic1.py](backend/apps/products/services/feed_logic1.py) реекспортує `fetch_smart_feed`.

### Група 4 (Seller, бан, лайки)

- **Файли:** [backend/apps/products/router.py](backend/apps/products/router.py) — `create_product` (multipart, `List[UploadFile]`), `toggle_like`.
- **Сервіси:** [backend/apps/products/services/moderation_redis.py](backend/apps/products/services/moderation_redis.py) (публікація в Redis після реалізації збереження файлів).
- **Не робіть:** передавати `UploadFile` у фонові задачі — лише шляхи/URL.

### Група 5 (Модерація & Telegram)

- **Файли:** [backend/apps/moderation/router.py](backend/apps/moderation/router.py) (`POST /moderation/decision`, заголовок `X-Bot-Secret`), [backend/apps/products/router.py](backend/apps/products/router.py) (`PATCH .../approve`, `PATCH .../reject` для бота), [backend/apps/users/router.py](backend/apps/users/router.py) (`list_notifications`).
- **SQLAdmin (перегляд таблиць):** [backend/apps/admin/admin_panel.py](backend/apps/admin/admin_panel.py) — не плутати з REST-модерацією; бот сюди не імпортується.
- **Конфіг:** [backend/config.py](backend/config.py) (`BOT_SECRET`, `API_BASE_URL`, `TG_*`).

### Група 6 (Orders & Chat)

- **Файли:** [backend/apps/orders/router.py](backend/apps/orders/router.py), [backend/apps/communication/router.py](backend/apps/communication/router.py) (HTTP + WebSocket).

### Інфраструктура (усі групи)

- **БД / сесії:** [backend/common/database.py](backend/common/database.py).
- **Redis (async):** [backend/common/redis_client.py](backend/common/redis_client.py).
- **Celery:** [backend/apps/celery/celery_app.py](backend/apps/celery/celery_app.py).
- **Міграції:** [backend/migrations/env.py](backend/migrations/env.py) імпортує `common.models` для `Base.metadata`.
- **Бот (клієнт API):** [backend/apps/bot/botkeyboard.py](backend/apps/bot/botkeyboard.py), [backend/apps/bot/bot.py](backend/apps/bot/bot.py).

## Узгодження з контрактом

- Альтернатива `POST /admin/moderation/decision`: у скелеті є `POST /api/v1/moderation/decision` ([backend/apps/moderation/router.py](backend/apps/moderation/router.py)) та `PATCH /api/v1/products/{id}/approve|reject` для бота.
- Оновіть **API-contract.md**, якщо змінюєте шляхи для фронту/бота.

## Визначення готовності (мінімум для здачі)

- [ ] Реалізовано JWT і залежність `get_current_user_id` без постійного 501.
- [ ] Реєстрація / логін відповідають контракту; паролі хешуються.
- [ ] `POST /products` зберігає файли в `static/`, товар у БД з `PENDING`, подія в Redis — за сценарієм викладача.
- [ ] Модерація оновлює статус / бан згідно з правилами проєкту.
- [ ] Celery-задача реально очищає прострочені бани (або оновлює поля в `users`).
- [ ] `alembic upgrade head` проходить на чистій БД.

Успіхів. Пишіть логіку поруч із docstrings — вони там саме як підказка.
