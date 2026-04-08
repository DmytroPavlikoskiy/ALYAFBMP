"""
Хендлери Telegram-бота (навчальний скелет).
API: базовий URL має збігатися з FastAPI — див. API-contract.md (/api/v1/...).
"""
import json

import httpx
from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from apps.bot.keyboards import get_menu_kb, get_sign_kb
from apps.bot.state import User_Log, User_Reg
from config import settings

router = Router()

_client = httpx.AsyncClient(base_url=settings.API_BASE_URL.rstrip("/"), timeout=30.0)

# Тимчасове сховище профілів у пам'яті (у проді — Redis / БД)
users: dict[int, dict] = {}


@router.message(CommandStart())
async def main_handler(message: types.Message):
    if message.from_user.id in users:
        user_name = users[message.from_user.id].get("first_name", "")
        await message.answer(f"👋 Вітаю знову, {user_name}!", reply_markup=await get_menu_kb())
    else:
        await message.answer(
            "Привіт! Будь ласка, авторизуйтесь або зареєструйтесь.",
            reply_markup=await get_sign_kb(),
        )


@router.message(F.text == "📝 Реєстрація")
async def reg_start(message: types.Message, state: FSMContext):
    await state.set_state(User_Reg.first_name)
    await message.answer("Введіть ваше ім'я:", reply_markup=ReplyKeyboardRemove())


@router.message(User_Reg.first_name)
async def reg_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.set_state(User_Reg.last_name)
    await message.answer("Введіть прізвище:")


@router.message(User_Reg.last_name)
async def reg_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await state.set_state(User_Reg.phone)
    await message.answer("Введіть номер телефону:")


@router.message(User_Reg.phone)
async def reg_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(User_Reg.email)
    await message.answer("Введіть email:")


@router.message(User_Reg.email)
async def reg_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(User_Reg.password)
    await message.answer("Створіть пароль:")


@router.message(User_Reg.password)
async def reg_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    # POST /api/v1/auth/register — тіло має відповідати схемі RegisterRequest
    payload = {**data, "tg_chat_id": message.chat.id}
    response = await _client.post("/api/v1/auth/register", json=payload)

    if response.status_code == 201:
        # TODO студенти: зберегти access/refresh у Redis (ключ tg_chat_id)
        await message.answer(f"✅ Реєстрація завершена, {data['first_name']}!", reply_markup=await get_menu_kb())
    else:
        await message.answer(f"Помилка реєстрації: {response.text}")
    await state.clear()


@router.message(F.text == "🔑 Увійти")
async def log_start(message: types.Message, state: FSMContext):
    await state.set_state(User_Log.email)
    await message.answer("Введіть ваш email:", reply_markup=ReplyKeyboardRemove())


@router.message(User_Log.email)
async def log_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(User_Log.password)
    await message.answer("Введіть пароль:")


@router.message(User_Log.password)
async def log_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    payload = {
        "email": data.get("email"),
        "password": message.text,
        "tg_chat_id": message.chat.id,
    }
    response = await _client.post("/api/v1/auth/login", json=payload)

    # TODO студенти: розпарсити JSON, зберегти токени, показати ім'я з /users/me
    found_user = None
    if response.status_code == 200:
        try:
            body = response.json()
            found_user = {"first_name": "користувач", "raw": body}
        except json.JSONDecodeError:
            found_user = None

    if found_user:
        await message.answer(
            f"✅ Успішний вхід! (заглушка) {found_user['first_name']}",
            reply_markup=await get_menu_kb(),
        )
        await state.clear()
    else:
        await message.answer("❌ Невірний email або пароль. Спробуйте ще раз або введіть /start")
