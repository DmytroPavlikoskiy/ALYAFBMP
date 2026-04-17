"""
Telegram bot handlers: registration, login, main menu.
API base URL must match FastAPI — see API-contract.md (/api/v1/...).
"""
from __future__ import annotations

import logging

import httpx
from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from apps.bot.bot_auth import delete_tokens, get_access_token, save_tokens
from apps.bot.keyboards import get_menu_kb, get_sign_kb
from apps.bot.moderation_cards import build_moderation_keyboard, send_moderation_card_to_chat
from apps.bot.state import User_Log, User_Reg
from config import settings

router = Router()
logger = logging.getLogger(__name__)

_client = httpx.AsyncClient(base_url=settings.API_BASE_URL.rstrip("/"), timeout=30.0)


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def main_handler(message: types.Message):
    token = await get_access_token(message.chat.id)
    if token:
        # Try to fetch user profile to confirm token is still valid
        try:
            resp = await _client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                me = resp.json()
                name = me.get("first_name", "")
                is_admin = me.get("role") == "ADMIN"
                await message.answer(
                    f"👋 Вітаю знову, {name}!",
                    reply_markup=await get_menu_kb(is_admin),
                )
                return
        except Exception as exc:
            logger.warning("Could not fetch /users/me: %s", exc)

    await message.answer(
        "Привіт! Будь ласка, авторизуйтесь або зареєструйтесь.",
        reply_markup=await get_sign_kb(),
    )


# ---------------------------------------------------------------------------
# Registration flow
# ---------------------------------------------------------------------------

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
    payload = {**data, "tg_chat_id": message.chat.id}

    response = await _client.post(
        "/api/v1/auth/register",
        json=payload,
        headers={"X-Bot-Secret": settings.BOT_SECRET},
    )

    if response.status_code == 201:
        # Registration doesn't return tokens; ask the user to log in
        await message.answer(
            f"✅ Реєстрація завершена, {data['first_name']}!\n"
            "Тепер увійдіть, щоб продовжити.",
            reply_markup=await get_sign_kb(),
        )
    else:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        await message.answer(f"❌ Помилка реєстрації: {detail}")
    await state.clear()


# ---------------------------------------------------------------------------
# Login flow
# ---------------------------------------------------------------------------

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

    if response.status_code == 200:
        body = response.json()
        access_token: str = body.get("access_token", "")
        refresh_token: str = body.get("refresh_token", "")

        await save_tokens(message.chat.id, access_token, refresh_token)

        # Fetch real profile
        first_name = "користувач"
        is_admin = False
        try:
            me_resp = await _client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if me_resp.status_code == 200:
                mj = me_resp.json()
                first_name = mj.get("first_name", first_name)
                is_admin = mj.get("role") == "ADMIN"
        except Exception as exc:
            logger.warning("Could not fetch /users/me after login: %s", exc)

        await message.answer(
            f"✅ Вітаємо, {first_name}!",
            reply_markup=await get_menu_kb(is_admin),
        )
    else:
        await message.answer(
            "❌ Невірний email або пароль. Спробуйте ще раз або введіть /start"
        )

    await state.clear()


# ---------------------------------------------------------------------------
# Main menu handlers
# ---------------------------------------------------------------------------

@router.message(F.text == "📋 Черга модерації")
async def moderation_queue_handler(message: types.Message):
    """Список товарів PENDING (лише ADMIN)."""
    token = await get_access_token(message.chat.id)
    if not token:
        await message.answer("Будь ласка, увійдіть спочатку.", reply_markup=await get_sign_kb())
        return
    me = await _client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    if me.status_code != 200 or me.json().get("role") != "ADMIN":
        await message.answer("⛔ Цей розділ доступний лише адміністраторам.")
        return

    resp = await _client.get(
        "/api/v1/bot-internal/pending-products",
        headers={"X-Bot-Secret": settings.BOT_SECRET},
    )
    if resp.status_code != 200:
        await message.answer("Не вдалося завантажити чергу. Спробуйте пізніше.")
        return
    items = resp.json()
    if not items:
        await message.answer("✅ Немає товарів, що очікують модерації.")
        return

    await message.answer(
        f"📋 <b>Черга модерації</b> (PENDING) — {len(items)} шт.\n"
        "Нижче — картки з кнопками «Схвалити» / «Відхилити».",
        parse_mode="HTML",
    )

    max_cards = 20
    for p in items[:max_cards]:
        pid = str(p["id"])
        imgs = p.get("images") or []
        image_url = imgs[0] if imgs else None
        caption = (
            f"📦 <b>{p['title']}</b>\n"
            f"💰 Ціна: {p['price']}\n"
            f"🆔 ID: {pid} · seller <code>{p['seller_id']}</code>"
        )
        keyboard = build_moderation_keyboard(pid)
        await send_moderation_card_to_chat(
            message.bot,
            chat_id=message.chat.id,
            caption=caption,
            keyboard=keyboard,
            image_url=image_url,
        )

    if len(items) > max_cards:
        await message.answer(
            f"… і ще {len(items) - max_cards} товар(ів). "
            "Після обробки оновіть чергу або відкрийте список у веб-адмінці."
        )


@router.message(F.text == "🛒 Магазин")
async def shop_handler(message: types.Message):
    token = await get_access_token(message.chat.id)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = await _client.get("/api/v1/products/feed?limit=5", headers=headers)
        if resp.status_code != 200:
            await message.answer("Не вдалося завантажити товари. Спробуйте пізніше.")
            return
        items = resp.json().get("feed_items", [])
        if not items:
            await message.answer("Наразі товарів немає.")
            return
        lines = []
        for item in items:
            lines.append(f"• <b>{item['title']}</b> — {item['price']} грн  (ID: {item['id']})")
        await message.answer(
            "🛒 <b>Останні оголошення:</b>\n" + "\n".join(lines),
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.exception("shop_handler error: %s", exc)
        await message.answer("Помилка завантаження магазину.")


@router.message(F.text == "⭐️ Вибране")
async def favorites_handler(message: types.Message):
    token = await get_access_token(message.chat.id)
    if not token:
        await message.answer("Будь ласка, увійдіть спочатку.", reply_markup=await get_sign_kb())
        return
    try:
        resp = await _client.get(
            "/api/v1/products_list/likes",
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            await message.answer("Не вдалося завантажити вибране.")
            return
        products = resp.json().get("products", [])
        if not products:
            await message.answer("Ваш список вибраного порожній.")
            return
        lines = [
            f"• <b>{p['product']['title']}</b> — {p['product']['price']} грн"
            for p in products
        ]
        await message.answer(
            "⭐️ <b>Ваше вибране:</b>\n" + "\n".join(lines),
            parse_mode="HTML",
        )
    except Exception as exc:
        logger.exception("favorites_handler error: %s", exc)
        await message.answer("Помилка завантаження вибраного.")


@router.message(F.text == "🚪 Вийти")
async def logout_handler(message: types.Message):
    await delete_tokens(message.chat.id)
    await message.answer(
        "До побачення! 👋 Ви вийшли з акаунту.",
        reply_markup=await get_sign_kb(),
    )
