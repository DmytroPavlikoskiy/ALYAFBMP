from fastapi import APIRouter, BackgroundTasks, FastAPI, Depends, Query
from typing import List, Optional, Dict
from apps.products.schemas import UserPref
from apps.products.models import UserPreference
from common.database import get_db
import uuid
from pydantic import Field


router = APIRouter()

@router.get("/categories")
async def get_category():
    cat = ""
    return cat

@router.post("/user/preferences")
async def choice_user_pref():
    user_pref = ""
    return user_pref

user_prefs = []

async def save_prefs(user_id: uuid.UUID, category_ids: List[int]):
    "Звертатись через db і сейвити в базу назі UserPreference"
    # db = await get_db()
    for user_pref_id in category_ids:
        await UserPreference.create(category_id=user_pref_id, user_id=user_id)
    return user_prefs


@app.post("/save-prefs")
async def save_user_prefs(user_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(save_prefs, user_id)
    
    return{
        "message":"Параметри користувача зберігаються у фоні",
        "user_prefs": user_prefs
    }


def user_check_ban(user_id) -> bool:
    "Дістаєш корисутвача або його uuid"
    "BanList.filter(user_id=user_id).first()"
    "Робиш перевірку якщо знайшовся по ід в бан лісті користувач,"
    "то return False, якщо такого корстувача не знайдено тоді return True"


@router.post("/create_product")
async def create_product(prod_data: Dict, check_ban: bool = Depends(user_check_ban)):
    if check_ban:
        "Дозволяєш створбвати"
    else:
        "Кидаєш відповідь json з msg = Нажали ви не можете зараз створити проукт, ви забанені ще сткільки часу."
    pass


@router.get("/get_products")
async def get_product(
    limit: int = Query(10, gt=0, le=100, description="Кількість товарів на сторінці"),
    page: int = Query(1),
    filter_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Дата у форматі YYYY-MM-DD"),
    price: float = Query(None),

):
    "витягуємо дані продуктів, якщо перша сторінка page=1,"
    "і limit=10: витягуємо перші 10 продуктів з 10 включно"
    "Якщо page=2, limit=10, значить витягуємо з 10 по 20 включно продукт і тд..."
    "Робимо перевірку чи нам прийшла filter_date, якщо filter_date є не = None то тоді,"
    "ми не робимо пагінацію, а просто віддаємо продукти по даті"
    "яка прийшла по полу created_at, поле created_at є істиною"

    "Робиш перевірку чи price is not None, якщо price прийшов то робиш перевіряєш чи прийшла filter_date"
    "Якщо прийшли і price і filter_date то ми перше фільтруємо по filter_date, а потім ті вітфільтровані дані фільтруємо по ціні"
    "Якщо прийшов лише price то просто фільтруємо по ціні"
    return {
        "limit": limit,
        "page": page,
        "filter_date": filter_date,
        "price": price if price is not None else None,
        "product": []
    }

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)