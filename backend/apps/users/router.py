from typing import List
from models import UserPerf
from fastapi import Header

# Group3
#POST
async def user_preferences():
    user = "Витягуєте юзера"
    user_prefs = "Приймаєте список обраних категорій користувача"
    #BagroundTask
    for user_pref_id in user_prefs:
        u_p = UserPerf.create(category_id=user_pref_id, user_id=user.id)
    return user_prefs


# Group1
#POST
async def register():
    user_data = "Приймаєте дані від фронта"
    #Валідація
    #Повернення даних + статус 201 "Реєстрація успішна!"
    pass


# Group1
#POST
async def login():
    user_data = "Приймаєте дані від фронта"
    #Валідація + перевірка чи такий користуча існує, чи співпадає пароль з хешем пароля в БД
    #Якщо все окей, створюємо access_tocken, refresh_tocken
    #Повернення даних + статус 200 Повертаємо всі дані User data + access_tocken, refresh_tocken
    pass



# Group1
#POST
async def logout():
    #Подивитись, як працює в JWT BlackList і реалізувати його.
    pass

# Group1
#GET
async def me():
    user = request.user
    return user
    #Повертаєте користувача, у вас користувач повертає JWTAuthMiddleware, його просто треба повернути.
    pass



#GET
async def get_admins(header: Header):
    #З хедера пробує дістати X-SECERT-BOT,
    # якщо є перевіряє на правильність по BOT_SECRET з env, якщо все окей, повретає дані про всіх адмінів,
    # якщо немає X-SECERT-BOT, або BOT_SECRET неправильний прилетів, ми забороняємо доступ до цих даних.
    user = request.user
    return user
    #Повертаєте користувача, у вас користувач повертає JWTAuthMiddleware, його просто треба повернути.
    pass

# def register_user(user_data):
#     import requests

#     resp = requests.post(url="http://localhost:8000/auth/regirster", json=user_data)
#     if resp.status_code == 200:
#         return {"status": 200, "message": "Вітаємо ви успішно зарейструвались", "is_correct": True}
#     else:
#         return {"status": 304, "message": "Упс щось пшло не так", "is_correct": False}