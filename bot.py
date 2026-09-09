import difflib
import telebot

from config import BOT_TOKEN, ADMIN_ID
from database import (
    init_db,
    add_reply,
    get_replies,
    get_reply,
    delete_reply
)
from keyboards import link_button, admin_panel


bot = telebot.TeleBot(BOT_TOKEN)

init_db()

# Temporary state for admin
admin_state = {}


# =========================
# NORMALIZE
# =========================

def normalize(text):
    text = text.lower().strip()

    replacements = {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
        "‌": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split())


# =========================
# FIND ANSWER
# =========================

def find_reply(user_text):

    user_text = normalize(user_text)

    replies = get_replies()

    if not replies:
        return None

    # Exact match
    for item in replies:

        question = normalize(item[1])

        if user_text == question:
            return item

    # Contains match
    for item in replies:

        question = normalize(item[1])

        if question in user_text:
            return item

        if user_text in question:
            return item

    # Similarity
    best = None
    best_score = 0

    for item in replies:

        question = normalize(item[1])

        score = difflib.SequenceMatcher(
            None,
            user_text,
            question
        ).ratio()

        if score > best_score:
            best_score = score
            best = item

    if best_score >= 0.60:
        return best

    return None


# =========================
# SEND REPLY
# =========================

def send_saved_reply(message, saved):

    _, question, answer, button_text, button_url = saved

    if button_text and button_url:

        keyboard = link_button(
            button_text,
            button_url
        )

        bot.send_message(
            message.chat.id,
            answer,
            reply_markup=keyboard
        )

    else:

        bot.send_message(
            message.chat.id,
            answer
        )


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    if message.from_user.id == ADMIN_ID:

        bot.send_message(
            message.chat.id,
            "🤖 پنل مدیریت منشی\n\n"
            "از دکمه‌های زیر استفاده کن:",
            reply_markup=admin_panel()
        )

    else:

        bot.reply_to(
            message,
            "سلام 👋❤️\n"
            "پیامت رو بفرست."
        )


# =========================
# PANEL
# =========================

@bot.message_handler(commands=["panel"])
def panel(message):

    if message.from_user.id != ADMIN_ID:
        return

    bot.send_message(
        message.chat.id,
        "🤖 پنل مدیریت:",
        reply_markup=admin_panel()
    )


# =========================
# CALLBACKS
# =========================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "⛔ دسترسی ندارید."
        )

        return

    if call.data == "add":

        admin_state[ADMIN_ID] = {
            "step": "question"
        }

        bot.send_message(
            call.message.chat.id,
            "➕ افزودن پاسخ\n\n"
            "❓ حالا سؤال را ارسال کن:"
        )

    elif call.data == "list":

        replies = get_replies()

        if not replies:

            bot.send_message(
                call.message.chat.id,
                "📭 هنوز پاسخی ثبت نشده."
            )

            return

        text = "📋 پاسخ‌های ثبت‌شده:\n\n"

        for item in replies:

            reply_id, question, answer, button_text, button_url = item

            text += (
                f"🆔 {reply_id}\n"
                f"❓ {question}\n"
                f"💬 {answer}\n"
            )

            if button_text:
                text += f"🔘 دکمه: {button_text}\n"

            text += "━━━━━━━━━━━━\n"

        bot.send_message(
            call.message.chat.id,
            text[:4000]
        )

    elif call.data == "delete":

        bot.send_message(
            call.message.chat.id,
            "🗑 برای حذف بنویس:\n\n"
            "/delete ID"
        )

    elif call.data == "stats":

        replies = get_replies()

        bot.send_message(
            call.message.chat.id,
            f"📊 آمار منشی\n\n"
            f"🧠 تعداد پاسخ‌ها: {len(replies)}"
        )

    bot.answer_callback_query(call.id)


# =========================
# ADMIN TEXT
# =========================

@bot.message_handler(
    func=lambda message:
    message.from_user.id == ADMIN_ID
)
def admin_message(message):

    text = message.text.strip()

    # Delete
    if text.startswith("/delete"):

        parts = text.split()

        if len(parts) != 2:

            bot.reply_to(
                message,
                "❌ مثال:\n/delete 3"
            )

            return

        try:
            reply_id = int(parts[1])
        except ValueError:

            bot.reply_to(
                message,
                "❌ ID باید عدد باشد."
            )

            return

        if delete_reply(reply_id):

            bot.reply_to(
                message,
                "🗑 پاسخ حذف شد."
            )

        else:

            bot.reply_to(
                message,
                "❌ چنین پاسخی وجود ندارد."
            )

        return

    # Add process
    state = admin_state.get(ADMIN_ID)

    if not state:
        return

    step = state["step"]

    if step == "question":

        state["question"] = text
        state["step"] = "answer"

        bot.reply_to(
            message,
            "💬 حالا جواب این سؤال را بفرست:"
        )

        return

    if step == "answer":

        state["answer"] = text
        state["step"] = "button_text"

        bot.reply_to(
            message,
            "🔘 اگر می‌خواهی دکمه داشته باشد، "
            "متن دکمه را بفرست.\n\n"
            "مثال:\n"
            "📣 ورود به کانال\n\n"
            "اگر دکمه نمی‌خواهی بنویس:\n"
            "ندارد"
        )

        return

    if step == "button_text":

        if normalize(text) == "ندارد":

            add_reply(
                state["question"],
                state["answer"]
            )

            del admin_state[ADMIN_ID]

            bot.reply_to(
                message,
                "✅ پاسخ بدون دکمه ذخیره شد."
            )

            return

        state["button_text"] = text
        state["step"] = "button_url"

        bot.reply_to(
            message,
            "🔗 حالا لینک دکمه را بفرست:"
        )

        return

    if step == "button_url":

        url = text.strip()

        if not (
            url.startswith("https://")
            or url.startswith("http://")
            or url.startswith("tg://")
        ):

            bot.reply_to(
                message,
                "❌ لینک معتبر نیست.\n"
                "مثلاً:\n"
                "https://t.me/YourChannel"
            )

            return

        add_reply(
            state["question"],
            state["answer"],
            state["button_text"],
            url
        )

        del admin_state[ADMIN_ID]

        bot.reply_to(
            message,
            "✅ پاسخ + دکمه با موفقیت ذخیره شد! 🚀"
        )


# =========================
# USERS
# =========================

@bot.message_handler(
    func=lambda message:
    message.from_user.id != ADMIN_ID
)
def user_message(message):

    if not message.text:

        bot.reply_to(
            message,
            "🤖 لطفاً پیام متنی ارسال کن."
        )

        return

    saved = find_reply(message.text)

    if saved:

        send_saved_reply(
            message,
            saved
        )

    else:

        bot.reply_to(
            message,
            "🤖 پیامت دریافت شد.\n"
            "آقا یاسین فعلاً سرش شلوغه و "
            "در اولین فرصت پاسخ می‌ده. 🙏"
        )


# =========================
# RUN
# =========================

print("🚀 Secretary Bot is starting...")
print("✅ Bot is online!")

bot.infinity_polling(
    skip_pending=True,
    timeout=30,
    long_polling_timeout=30
)
