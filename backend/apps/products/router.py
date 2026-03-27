from products.services.get_smart_feed import get_smart_feed
from models import UserPerf


#GET
async def get_category():
    cat = "Берез всы категорії"
    return cat


#Group4
#POST
async def products_feed():
    products = "Дістаємо з бази всі продукти"
    user_pref = "Дістаємо з UserPerf по user.id список категорій"
    sorted_for_user_pref_prod = get_smart_feed(products, user_pref)
    return sorted_for_user_pref_prod



#Group3
#GET
async def get_product(pord_id):
    product = "Дістаємо продукт по pord_id"
    return product


#Group4
#POST
async def create_product():
    data_product = "Приймаєте від фронта дані на стоврення"
    #З хедера пробує дістати X-SECERT-BOT,
    # якщо є перевіряє на правильність по BOT_SECRET з env, якщо все окей, повретає дані про всіх адмінів,
    # якщо немає X-SECERT-BOT, або BOT_SECRET неправильний прилетів, ми забороняємо доступ до цих даних.
    #Створюєте продукт можете зробити також через BackgroundTask
    #відповідь повертати одразу, не чекаючи на створення продукту



#Group4
#POST
async def pre_create_product():
    chanel_name = "chanel_precreate_prod"
    data_product = "Приймаєте від фронта дані на стоврення"

    #BackgroundTask - Передаємо дані data_product в таску, і в BackgroundTask - тасці ми записуємо ці дані в redis chanel_name
    #відповідь повертати одразу, не чекаючи на створення продукту

