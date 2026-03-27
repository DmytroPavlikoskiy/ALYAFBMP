


#Group1
class JWTAuthMiddleware():
    #Дістати з хедера Bearer JWT Tocken
    #Перверірити його на валідність + BlackList(зробити перевірку, чи цей токен не є в блек лісті, якщо є 401) і на (TTL)
    #Якщо все окей віддаємо користувача, якщо щось не ок, 401 Unauthorized
    pass