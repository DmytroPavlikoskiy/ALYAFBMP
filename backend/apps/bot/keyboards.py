from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


async def get_sign_kb() -> ReplyKeyboardMarkup:
    sign_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔑 Увійти"), KeyboardButton(text="📝 Реєстрація")]
        ],
        resize_keyboard=True,
    )
    return sign_kb


async def get_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Головне меню; для role ADMIN — додатковий рядок модерації."""
    rows = [
        [KeyboardButton(text="🛒 Магазин")],
        [KeyboardButton(text="⭐️ Вибране")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="📋 Черга модерації")])
    rows.append([KeyboardButton(text="🚪 Вийти")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
