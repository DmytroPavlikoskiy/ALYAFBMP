from fastapi import APIRouter, BackgroundTasks, FastAPI
from typing import List

app = FastAPI()
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

async def save_prefs():
    for user_pref_id in user_prefs:
        await UserPerf.create(category_id=user_pref_id, user_id=user_id)
    return user_prefs

@app.post("/save-prefs")
async def save_user_prefs(user_id: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(save_prefs, user_id)
    
    return{
        "message":"Параметри користувача зберігаються у фоні",
        "user_prefs": user_prefs
    }

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)