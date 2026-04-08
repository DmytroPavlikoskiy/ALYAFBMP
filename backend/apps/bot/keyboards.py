from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


async def get_sign_kb() -> ReplyKeyboardMarkup:
    ""
    sign_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔑 Увійти"), KeyboardButton(text="📝 Реєстрація")]
    ],
    resize_keyboard=True
)
    return sign_kb


async def get_menu_kb():
    "main_mz"
    menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Магазин")],
        [KeyboardButton(text="⭐️ Вибране")],
        [KeyboardButton(text="🚪 Вийти")]
    ],
    resize_keyboard=True
)
    return menu_kb
