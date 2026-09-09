from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def link_button(text, url):
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text,
            url=url
        )
    )

    return keyboard


def admin_panel():
    keyboard = InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        InlineKeyboardButton("➕ افزودن پاسخ", callback_data="add"),
        InlineKeyboardButton("📋 پاسخ‌ها", callback_data="list")
    )

    keyboard.add(
        InlineKeyboardButton("🗑 حذف پاسخ", callback_data="delete"),
        InlineKeyboardButton("📊 آمار", callback_data="stats")
    )

    return keyboard
