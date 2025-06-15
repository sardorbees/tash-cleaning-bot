import json
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Шаги диалога
CLEAN_TYPE, NAME, PHONE, ADDRESS, DATE_TIME, COMMENT, ASK_QUESTION = range(7)


# ADMIN_GROUP_ID = 1756108441

import os

TOKEN = os.getenv("8047716790:AAF3Orl4sM7lMe6IMxHbybYcsh4aSpRhIRA")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID"))

# Приветственная анимация (если есть)
ANIMATION_PATH = "animation.gif"

# Загрузка FAQ
with open("faq.json", encoding="utf-8") as f:
    FAQ = json.load(f)

# === Хендлер /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(ANIMATION_PATH, "rb") as gif:
            await update.message.reply_animation(gif)
    except:
        pass

    keyboard = [
        ["🧼 Стандартная уборка", "🧹 Генеральная уборка"],
        ["❓ Часто задаваемые вопросы", "💬 Задать вопрос"]
    ]
    await update.message.reply_text(
        "Здравствуйте! 👋\nВыберите тип уборки:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CLEAN_TYPE

# === Шаги формы ===
async def clean_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["type"] = update.message.text
    await update.message.reply_text("Введите ваше имя:")
    return NAME

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Введите ваш номер телефона:")
    return PHONE

async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text(
        "Отправьте адрес (геолокация или текст):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("📍 Отправить локацию", request_location=True)]], resize_keyboard=True)
    )
    return ADDRESS

async def address_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        context.user_data["address"] = f"https://maps.google.com/?q={lat},{lon}"
    else:
        context.user_data["address"] = update.message.text
    await update.message.reply_text("Введите дату и время уборки:")
    return DATE_TIME

async def datetime_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["datetime"] = update.message.text
    await update.message.reply_text("Добавьте комментарий (если есть):")
    return COMMENT

async def comment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["comment"] = update.message.text

    data = context.user_data
    text = (
        "🧾 Новая заявка на уборку:\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🏠 Адрес: {data['address']}\n"
        f"📅 Дата/время: {data['datetime']}\n"
        f"🧽 Тип: {data['type']}\n"
        f"💬 Комментарий: {data['comment']}"
    )

    await update.message.reply_text("Спасибо! Ваша заявка принята ✅", reply_markup=ReplyKeyboardRemove())
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=text)
    return ConversationHandler.END

# === Часто задаваемые вопросы ===
async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faq_text = "\n\n".join([f"❓ {q}\n💡 {a}" for q, a in FAQ.items()])
    await update.message.reply_text(f"📚 Часто задаваемые вопросы:\n\n{faq_text}")
    return CLEAN_TYPE

# === Пользователь задаёт вопрос ===
async def ask_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите свой вопрос, мы ответим как можно скорее:")
    return ASK_QUESTION

async def question_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    context.user_data["question_user"] = user.id
    context.user_data["question_msg_id"] = update.message.message_id

    text = (
        f"📨 Новый вопрос от @{user.username or user.first_name} (ID: {user.id}):\n"
        f"{update.message.text}"
    )
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=text)
    await update.message.reply_text("Ваш вопрос получен! ⏳ Ожидайте ответа.")
    return CLEAN_TYPE

# === Команда /cancel ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# === Запуск бота ===
def main():
    app = ApplicationBuilder().token("8047716790:AAF3Orl4sM7lMe6IMxHbybYcsh4aSpRhIRA").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CLEAN_TYPE: [
                MessageHandler(filters.Regex("^(🧼|🧹)"), clean_type_handler),
                MessageHandler(filters.Regex("❓"), faq_handler),
                MessageHandler(filters.Regex("💬"), ask_question_handler),
            ],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler)],
            ADDRESS: [
                MessageHandler(filters.LOCATION, address_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, address_handler)
            ],
            DATE_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, datetime_handler)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment_handler)],
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
