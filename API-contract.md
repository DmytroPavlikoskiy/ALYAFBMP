📝 API Contract (v1.0) — Marketplace Project

```python
{
  "project": "Marketplace MVP (OLX Style)",
  "version": "1.0.0",
  "base_url": "/api/v1",
  "auth_scheme": "Bearer JWT",
  "endpoints": {
    "auth": [
      {
        "method": "POST",
        "path": "/auth/register",
        "description": "Реєстрація нового користувача",
        "request_body": {
          "email": "string",
          "password": "string",
          "first_name": "string",
          "last_name": "string",
          "phone": "string"
        },
        "responses": {
          "201": { "user_id": "uuid" },
          "400": { "error": "USER_ALREADY_EXISTS" }
        }
      },
      {
        "method": "POST",
        "path": "/auth/login",
        "description": "Логінація та отримання токенів",
        "request_body": {
          "email": "string",
          "password": "string"
        },
        "responses": {
          "200": { "access": "jwt_token", "refresh": "jwt_token" },
          "401": { "error": "INVALID_CREDENTIALS" }
        }
      }
    ],
    "users": [
      {
        "method": "GET",
        "path": "/users/me",
        "description": "Дані профілю, статус бану та обрані категорії",
        "responses": {
          "200": {
            "id": "uuid",
            "first_name": "string",
            "is_banned": "boolean",
            "banned_until": "iso_date",
            "selected_categories": [1, 2, 3]
          }
        }
      },
      {
        "method": "POST",
        "path": "/users/me/preferences",
        "description": "Збереження категорій, обраних у модалці",
        "request_body": { "category_ids": [1, 5] },
        "responses": { "200": "success" }
      },
      {
        "method": "GET",
        "path": "/users/me/notifications",
        "description": "Список повідомлень (approve/reject/ban)",
        "responses": {
          "200": [{ "id": "int", "text": "string", "type": "INFO|WARNING", "created_at": "iso_date" }]
        }
      }
    ],
    "categories": [
      {
        "method": "GET",
        "path": "/categories",
        "description": "Список усіх доступних категорій для модалки",
        "responses": { "200": [{ "id": "int", "name": "string", "icon_url": "string" }] }
      }
    ],
    "products": [
      {
        "method": "GET",
        "path": "/products/feed",
        "description": "Головна стрічка (спочатку обрані категорії, потім решта)",
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
        "description": "Деталі товару + інфо про продавця",
        "responses": {
          "200": {
            "id": "int",
            "title": "string",
            "description": "string",
            "price": "float",
            "seller": { "id": "uuid", "name": "string" },
            "status": "ACTIVE|PENDING|REJECTED"
          }
        }
      },
      {
        "method": "POST",
        "path": "/products",
        "description": "Створення оголошення (йде на модерацію)",
        "request_body": {
          "title": "string",
          "description": "string",
          "price": "float",
          "category_id": "int",
          "images": ["url"]
        },
        "responses": { "201": { "id": "int", "status": "PENDING" }, "403": { "error": "USER_BANNED" } }
      },
      {
        "method": "POST",
        "path": "/products/{id}/like",
        "description": "Додати/видалити з обраного",
        "responses": { "200": { "is_liked": "bool" } }
      }
    ],
    "orders": [
      {
        "method": "POST",
        "path": "/orders",
        "description": "Створення замовлення",
        "request_body": { "product_id": "int" },
        "responses": { "201": { "order_id": "int" } }
      }
    ],
    "moderation_internal": [
      {
        "method": "POST",
        "path": "/admin/moderation/decision",
        "description": "Ендпоінт для ТГ бота (Webhook)",
        "request_body": {
          "product_id": "int",
          "action": "APPROVE|REJECT",
          "reason": "string",
          "ban_user": "bool",
          "ban_days": 3
        },
        "responses": { "200": "ok" }
      }
    ],
    "chats": [
      {
        "method": "GET",
        "path": "/chats",
        "description": "Список усіх чатів користувача",
        "responses": { "200": [{ "chat_id": "uuid", "last_message": "string", "opponent": "string" }] }
      },
      {
        "method": "WS",
        "path": "/ws/chat/{chat_id}",
        "description": "WebSocket для реалтайм спілкування",
        "message_format": { "sender_id": "uuid", "text": "string", "sent_at": "iso_date" }
      }
    ]
  }
}
```

👥 Розподіл задач між групами (Team Lead Plan)
Кожна група складається з 3 дітей: Developer A (Backend/Logic), Developer B (API/Validation), Developer C (Database/Testing).


(Сніжана, Ксенія, Юра)
Група 1: Auth & User Security
Дитина 1: Реалізація JWT (login, register, token refresh).

Дитина 2: Модель користувача (User) та ролі (ADMIN/USER).

Дитина 3: Система валідації паролів та пошти.


-
Група 2: Category Picker & Profile
Дитина 1: Ендпоінти для категорій (GET /categories).

Дитина 2: Збереження преференцій (preferences) у БД.

Дитина 3: Реалізація Update профілю та завантаження аватарки.

(Катя, Настя, Марта)
Група 3: Smart Feed & Search
Дитина 1: Алгоритм Smart Feed (сортування за обраними категоріями).

Дитина 2: Ендпоінт детальної сторінки товару (Product Detail).

Дитина 3: Система пагінації та фільтрація за ціною/датою.



(Женя, Тимофій, Матвій)
Група 4: Seller System & Moderation Logic
Дитина 1: Ендпоінт створення товару (POST /products) та статус PENDING.

Дитина 2: Логіка "Банку" (Penalty): перевірка banned_until при створенні.

Дитина 3: Реалізація лайків (Wishlist) — окрема таблиця в БД.


(Давид, Женя, Миша, Женя.Б)
Група 5: Admin & Telegram Integration
Дитина 1: Ендпоінт для Telegram Webhook (обробка рішень адміна).

Дитина 2: Надсилання повідомлень у ТГ канал (через бібліотеку httpx або requests).

Дитина 3: Система сповіщень (Notifications) у профілі клієнта.



Група 6: Orders & Real-time Chat
Дитина 1: Створення замовлень (Orders) та історія покупок.

Дитина 2: WebSocket сервер (через FastAPI) для миттєвих повідомлень.

Дитина 3: Збереження історії чатів у базі даних.

🚦 Як працювати, щоб не заважати один одному:
Git Branches: Кожна група працює у своїй гілці (feature/group1-auth, feature/group2-cats).

Shared Models: Спершу всі разом створіть один файл models.py з усіма таблицями (БД), а потім кожен розробляє свої ендпоінти.

Mocking: Якщо Групі 6 потрібні товари, які ще не доробила Група 3, вони просто використовують фейкові дані (Mock) для тестів.


``` SQL

🗄 Database Schema (SQL) — Marketplace MVP

-- 1. Користувачі та Ролі
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'USER', -- 'USER' або 'ADMIN'
    avatar_url TEXT,
    banned_until TIMESTAMP WITH TIME ZONE DEFAULT NULL, -- Час закінчення бану
    ban_reason TEXT, -- Причина бану від адміна
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Категорії товарів
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    icon_url TEXT
);

-- 3. Зв'язок Користувач-Категорія (для "Smart Feed")
-- Це Many-to-Many: один юзер може обрати багато категорій
CREATE TABLE user_preferences (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, category_id)
);

-- 4. Товари (Products)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    seller_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(12, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING', -- 'PENDING', 'ACTIVE', 'REJECTED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Зображення товарів
CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL
);

-- 6. Обране (Wishlist)
CREATE TABLE wishlist (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, product_id)
);

-- 7. Замовлення (Orders)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    buyer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'CREATED', -- 'CREATED', 'COMPLETED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Повідомлення / Сповіщення (Notifications)
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'INFO', -- 'INFO', 'WARNING' (для бану)
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Чати та Повідомлення (WebSocket Backend)
CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    buyer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    seller_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

```


🛠 Поради для кожної групи по роботі з цією БД:
Група 1 & 2: Ви працюєте з таблицями users, categories та user_preferences. Зверніть увагу на поле banned_until — це ваш головний інструмент контролю.

Група 3 & 4: Ваша база — products, product_images та wishlist. Для "Smart Feed" вам знадобиться SQL-запит, який робить LEFT JOIN таблиці user_preferences.

Група 5 (Admin): Ви будете апдейтити поле status у таблиці products та додавати записи в notifications і users (для бану).

Група 6 (Chats): Ваші таблиці chats та messages. Пам'ятайте, що чат прив'язаний до товару, щоб покупець і продавець розуміли, про що йде мова.

💡 Лайфхак для швидкості (SQL Indexes):
Додайте ці індекси, щоб сайт "літав", коли товарів стане багато:

CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_messages_chat ON messages(chat_id);