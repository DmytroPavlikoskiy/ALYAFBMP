📝 API Contract (v1.1) — Навчальний Marketplace

Ціль: один джерело правди для бекенду (FastAPI), Telegram-бота та фронтенду. Усі шляхи нижче — відносно `base_url`.

---

## 1. Глобальні правила

### 1.1. Базова адреса та версія

- **base_url**: `/api/v1`
- **version**: `1.1.0`

### 1.2. Автентифікація клієнта (веб / мобільний додаток)

- **Схема**: `Authorization: Bearer <JWT access token>`
- Токен видається після `POST /auth/login` та `POST /auth/register` (поле `access`).
- Ендпоінти, які стосуються конкретного користувача (`/users/me`, створення товару тощо), вимагають валідний JWT.

### 1.3. Інтеграція Telegram-бота з API

**A) Секрет бота (обов’язково для всіх запитів «система бот → бекенд», які не від імені користувача)**

- У кожному такому запиті бекенд перевіряє **`BOT_SECRET`**.
- Рекомендовано передавати заголовком:  
  `X-Bot-Secret: <BOT_SECRET>`  
  (допустимо й поле в JSON тіла для навчального проєкту, але один спосіб треба зафіксувати в коді й не змішувати без потреби).

**B) JWT користувача в боті**

- Після успішної **реєстрації або логіну через бота** бот отримує з API поля `access` (і за бажання `refresh`).
- Бот **зберігає** `access` (JWT) у сховищі з швидким доступом — **рекомендовано Redis**, ключ на кшталт `bot:jwt:{tg_chat_id}`.
- Будь-який запит до API **від імені залогіненого користувача** з бота має містити:  
  `Authorization: Bearer <access>`  
  плюс бекенд може звіряти `tg_chat_id` з профілем користувача, якщо передається окремо.

**C) Редис і модерація**

- Після створення оголошення бекенд зберігає товар зі статусом **`PENDING`** і публікує повідомлення в канал Redis **`moderation_channel`** (формат JSON узгодити в команді, мінімум: `product_id`, `title`, `seller_id`, `image_urls` / прев’ю).
- **Telegram-бот підписаний** на `moderation_channel` (окремий процес/воркер). Отримавши подію, бот:
  1. Викликає **`GET /get_admins`** (з `BOT_SECRET`), щоб отримати список адміністраторів для розсилки.
  2. Надсилає адмінам у Telegram інформацію про новий товар і кнопки **`APPROVE`** / **`REJECT`**.
  3. Після натискання викликає **`POST /check_status_product`** (з `BOT_SECRET`) з рішенням.

---

## 2. Ендпоінти (машиночитний огляд)

```json
{
  "project": "Marketplace (навчальний)",
  "version": "1.1.0",
  "base_url": "/api/v1",
  "auth_scheme_client": "Bearer JWT",
  "bot_to_api": {
    "required_header": "X-Bot-Secret: BOT_SECRET",
    "user_requests_from_bot": "Authorization: Bearer access_jwt"
  },
  "redis": {
    "moderation_channel": "moderation_channel"
  },
  "endpoints": {
    "auth": [
      {
        "method": "POST",
        "path": "/auth/register",
        "description": "Реєстрація. Якщо реєстрація з Telegram-бота — tg_chat_id обов'язковий.",
        "request_body": {
          "email": "string",
          "password": "string",
          "first_name": "string",
          "last_name": "string",
          "phone": "string",
          "tg_chat_id": "int | null"
        },
        "rules": "Якщо запит ініційовано ботом (або поле tg_chat_id передано), tg_chat_id обов'язковий і зберігається в users.tg_chat_id (унікальність у межах БД).",
        "responses": {
          "201": { "user_id": "uuid", "access": "jwt", "refresh": "jwt" },
          "400": { "error": "USER_ALREADY_EXISTS | VALIDATION_ERROR" }
        }
      },
      {
        "method": "POST",
        "path": "/auth/login",
        "description": "Логін. Для входу через бота — передати tg_chat_id для прив'язки/оновлення чату.",
        "request_body": {
          "email": "string",
          "password": "string",
          "tg_chat_id": "int | null"
        },
        "rules": "Якщо tg_chat_id передано — оновити users.tg_chat_id для цього користувача.",
        "responses": {
          "200": { "access": "jwt", "refresh": "jwt" },
          "401": { "error": "INVALID_CREDENTIALS" }
        }
      }
    ],
    "bot_internal": [
      {
        "method": "GET",
        "path": "/get_admins",
        "description": "Список адміністраторів для розсилки в Telegram (викликає бот після нової події в moderation_channel).",
        "auth": "X-Bot-Secret only (не JWT користувача)",
        "responses": {
          "200": {
            "admins": [
              { "user_id": "uuid", "tg_chat_id": "int | null", "email": "string" }
            ]
          },
          "401": { "error": "INVALID_BOT_SECRET" }
        }
      },
      {
        "method": "POST",
        "path": "/check_status_product",
        "description": "Застосування рішення модерації з бота: APPROVE — оновити статус товару; REJECT — видалити товар і забанити продавця на 3 дні.",
        "auth": "X-Bot-Secret only",
        "request_body": {
          "product_id": "int",
          "action": "APPROVE | REJECT"
        },
        "behavior": {
          "APPROVE": "Встановити products.status = 'APPROVE' (товар видимий у стрічці).",
          "REJECT": "Видалити запис продукту (і залежні product_images). Встановити users.banned_until = now() + 3 days для продавця; опційно notification та ban_reason."
        },
        "responses": {
          "200": { "status": "ok" },
          "401": { "error": "INVALID_BOT_SECRET" },
          "404": { "error": "PRODUCT_NOT_FOUND" }
        }
      }
    ],
    "users": [
      {
        "method": "GET",
        "path": "/users/me",
        "description": "Профіль, бан, обрані категорії",
        "responses": {
          "200": {
            "id": "uuid",
            "first_name": "string",
            "tg_chat_id": "int | null",
            "is_banned": "boolean",
            "banned_until": "iso_date | null",
            "selected_categories": [1, 2, 3]
          }
        }
      },
      {
        "method": "POST",
        "path": "/users/me/preferences",
        "description": "Збереження категорій з модального вікна (впливає на порядок у стрічці)",
        "request_body": { "category_ids": [1, 5] },
        "responses": { "200": { "success": true } }
      },
      {
        "method": "GET",
        "path": "/users/me/notifications",
        "description": "Сповіщення (модерація, бан тощо)",
        "responses": {
          "200": [{ "id": "int", "text": "string", "type": "INFO|WARNING", "created_at": "iso_date" }]
        }
      }
    ],
    "categories": [
      {
        "method": "GET",
        "path": "/categories",
        "description": "Категорії для модалки",
        "responses": { "200": [{ "id": "int", "name": "string", "icon_url": "string" }] }
      }
    ],
    "products": [
      {
        "method": "GET",
        "path": "/products/feed",
        "description": "Стрічка: спочатку товари з обраних категорій (пріоритет зверху), далі решта; показувати лише схвалені товари (status APPROVE), якщо не узгоджено інше.",
        "query_params": ["page", "limit", "category_id"],
        "responses": {
          "200": {
            "items": [{ "id": "int", "title": "string", "price": "float", "is_priority": "bool" }],
            "total": "int"
          }
        }
      },
      {
        "method": "GET",
        "path": "/products/{id}",
        "description": "Картка товару",
        "responses": {
          "200": {
            "id": "int",
            "title": "string",
            "description": "string",
            "price": "float",
            "seller": { "id": "uuid", "name": "string" },
            "status": "APPROVE|PENDING|REJECTED"
          }
        }
      },
      {
        "method": "POST",
        "path": "/products",
        "description": "Створення оголошення → status PENDING; після збереження — публікація в Redis moderation_channel",
        "request_body": {
          "title": "string",
          "description": "string",
          "price": "float",
          "category_id": "int",
          "images": ["url"]
        },
        "responses": {
          "201": { "id": "int", "status": "PENDING" },
          "403": { "error": "USER_BANNED" }
        }
      },
      {
        "method": "POST",
        "path": "/products/{id}/like",
        "description": "Обране",
        "responses": { "200": { "is_liked": "bool" } }
      }
    ],
    "orders": [
      {
        "method": "POST",
        "path": "/orders",
        "request_body": { "product_id": "int" },
        "responses": { "201": { "order_id": "int" } }
      }
    ],
    "chats": [
      {
        "method": "GET",
        "path": "/chats",
        "responses": { "200": [{ "chat_id": "uuid", "last_message": "string", "opponent": "string" }] }
      },
      {
        "method": "WS",
        "path": "/ws/chat/{chat_id}",
        "message_format": { "sender_id": "uuid", "text": "string", "sent_at": "iso_date" }
      }
    ]
  }
}