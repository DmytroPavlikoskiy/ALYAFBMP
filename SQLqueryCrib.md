1. Отримання одного об'єкта за ID
Найпростіший спосіб дістати конкретний запис.

Python
# Отримати продукт за ID
```python
product = await db.get(Product, product_id)

if product:
    print(product.title)

```

2. Пошук (SELECT) з фільтрацією
Використовуємо функцію select.

Python

```python
from sqlalchemy import select

# Знайти всі товари, де статус "PENDING"
stmt = select(Product).where(Product.status == "PENDING")
result = await db.execute(stmt)

# .scalars() робить список об'єктів, а не кортежів
products = result.scalars().all() 

```

3. Отримання лише першого результату
Корисно для перевірки пошти або ID, які мають бути унікальними.

Python
```python

stmt = select(User).where(User.email == "test@test.com")
result = await db.execute(stmt)

# .first() або .scalar_one_or_none()
user = result.scalar_one_or_none()

```

4. Оновлення об'єкта (UPDATE)
В SQLAlchemy 2.0 ми просто змінюємо атрибут об'єкта, який вже завантажений у сесію.

Python
# 1. Дістаємо
product = await db.get(Product, product_id)

```python
if product:
    # 2. Змінюємо
    product.status = "APPROVE"
    product.updated_at = datetime.now()
    
    # 3. Зберігаємо (у вашому get_db commit робиться автоматично, але можна і вручну)
    await db.commit()
```

5. Видалення запису (DELETE)
Python

```python
from sqlalchemy import delete

# Видалити конкретний бан
stmt = delete(BanList).where(BanList.user_id == user_id)
await db.execute(stmt)
await db.commit()
6. Створення нового запису (INSERT)
Python
new_ban = BanList(user_id=some_uuid, reason="Spam")
db.add(new_ban)

await db.commit()
# Після commit ID буде доступний автоматично
print(new_ban.id)

```