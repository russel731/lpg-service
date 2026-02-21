from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def roles_keyboard(lang: str):
    if lang == "kz":
        driver = "🚗 Жүргізуші"
        owner = "⛽ АГЗС иесі"
    else:
        driver = "🚗 Водитель"
        owner = "⛽ Владелец АГЗС"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=driver, callback_data="role_driver")],
            [InlineKeyboardButton(text=owner, callback_data="role_owner")],
        ]
    )