import json
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler, ContextTypes

# Шаги диалога
CLEAN_TYPE, NAME, PHONE, ADDRESS, DATE_TIME, COMMENT, ASK_QUESTION, HOUSE_TYPE = range(8)
pending_questions = {}


# Замените этим ID вашей Telegram-группы
ADMIN_GROUP_ID = 1756108441  # пример
import os
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "1756108441"))

# chat_id=1756108441,
# Приветственная анимация (если есть)

ASKING_QUESTION = 1
VIDEO_PATH = "/home/sdhoijfidnhindhijtn/video2.mp4"



user_questions = {}

ANIMATION_PATH = "animation.gif"
from database import Session, User
import logging
logging.basicConfig(level=logging.INFO)

with open("faq.json", encoding="utf-8") as f:
    FAQ = json.load(f)

# === Хендлер /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    session = Session()

    user_type = update.message.text
    context.user_data["house_type"] = user_type

    await update.message.reply_text(
        "Спасибо! Ваша заявка почти готова. Мы свяжемся с вами в ближайшее время."
    )

    existing = session.query(User).filter_by(telegram_id=tg_user.id).first()
    if not existing:
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name
        )
        session.add(user)
        session.commit()

        # Отправляем уведомление админу
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🆕 Новый пользователь:\n👤 {tg_user.full_name}\n🆔 @{tg_user.username or 'Без username'}"
    )

    await update.message.reply_text(
    "Добро пожаловать! Вы успешно зарегистрированы.\nВы можете начать оформление заявки на уборку!"
    )

    welcome_text = (
        "Xush kelibsz?\n"
        "TashClean!\n"
        "🥳 Tabriklaymiz!!! Sizga 🎁 50% chegirma taqdim etildi.\n"
        "📑 Promokodingiz: Cleaing10012 nusxalab botga yuboring.\n"
        "/start qayta ishga tushuring.\n"
    )
    keyboard = [
        [InlineKeyboardButton("🎥 Посмотреть видео", callback_data="show_video")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать! Вы можете посмотреть наше видео:", reply_markup=reply_markup)
    try:
        with open(ANIMATION_PATH, "rb") as gif:
            await update.message.reply_animation(gif)
    except:
        pass

    keyboard = [
        ["🧼 Стандартная уборка", "🧹 Генеральная уборка"],
        ["❓ Часто задаваемые вопросы", "💬 Задать вопрос"]
    ]
    await update.message.reply_text(welcome_text)
    await update.message.reply_text(
        "Здравствуйте! 👋\nВыберите тип уборки:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    await update.message.reply_text(
        "Ответьте на несколько вопросов, чтобы оформить заявку.\nКакой вам уборка?"
    )
    return CLEAN_TYPE

# === Шаги формы ===
async def clean_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["type"] = update.message.text
    await update.message.reply_text("Введите ваше имя:")
    return NAME

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "show_video":
        with open(VIDEO_PATH, 'rb') as video:
            await context.bot.send_video(
                chat_id=query.message.chat.id,
                video=video,
                caption="📽 Это наша работа — можете посмотреть"
            )

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
        f"Тип жилья: {context.user_data.get('house_type')}"
    )

    await update.message.reply_text("Спасибо! Ваша заявка принята ✅", reply_markup=ReplyKeyboardRemove())
    await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=text)
    return ConversationHandler.END

# === Часто задаваемые вопросы ===
async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    question = update.message.text

    # Отправляем админу
    sent = await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"💬 Вопрос от @{user.username or user.first_name} (ID: {user.id}):\n\n{question}"
    )

    # Сохраняем: message_id -> user_id
    user_questions[sent.message_id] = user.id

    await update.message.reply_text("✅ Ваш вопрос отправлен. Мы ответим в ближайшее время.")
    return ConversationHandler.END

async def forward_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        original_message_id = update.message.reply_to_message.message_id
        reply_text = update.message.text

        user_id = user_questions.get(original_message_id)

        if user_id:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"💬 Ответ на ваш вопрос:\n\n{reply_text}"
                )
                await update.message.reply_text("✅ Ответ отправлен пользователю.")
            except Exception as e:
                await update.message.reply_text("❌ Не удалось отправить ответ пользователю.")
        else:
            await update.message.reply_text("⚠️ Не найден ID пользователя.")

# === Пользователь задаёт вопрос ===
async def ask_question_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    question = update.message.text

    user_questions[user_id] = question  # сохраняем вопрос

    # Уведомим админа
    text = f"❓ Новый вопрос от @{update.effective_user.username or 'без username'} (ID: {user_id}):\n\n{question}\n\n" \
           f"Чтобы ответить: /reply {user_id} ваш_ответ"

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    await update.message.reply_text("Ваш вопрос принят. Мы скоро ответим.")

async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /reply <user_id> <ваш ответ>")
        return

    try:
        user_id = int(context.args[0])
        answer = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=user_id, text=f"📩 Ответ на ваш вопрос:\n\n{answer}")
        await update.message.reply_text("✅ Ответ отправлен.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка отправки: {e}")

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        original_message = update.message.reply_to_message.text
        try:
            user_id = int(original_message.split("ID: ")[-1])
        except Exception:
            await update.message.reply_text("❌ Не удалось определить пользователя для ответа.")
            return

        response_text = update.message.text.replace("/reply", "").strip()
        if not response_text:
            await update.message.reply_text("✏️ Пожалуйста, укажите текст ответа после /reply.")
            return

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"💬 Ответ от администратора:\n\n{response_text}",
                parse_mode=ParseMode.HTML
            )
            await update.message.reply_text("✅ Ответ отправлен пользователю.")
        except Exception as e:
            await update.message.reply_text(f"❌ Не удалось отправить сообщение. Ошибка: {e}")
    else:
        await update.message.reply_text("❗ Используйте /reply в ответ на сообщение с вопросом.")

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
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

async def ask_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пожалуйста, введите свой вопрос:")
    return ASKING_QUESTION


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Спасибо за сообщение! Мы с вами свяжемся.")


async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧽 Часто задаваемые вопросы:\n\n"
        "❓ Какие виды уборки вы предоставляете?\n"
        "— Стандартная и генеральная уборка.\n\n"
        "❓ Сколько стоит уборка?\n"
        "— Зависит от площади и типа уборки. Мы свяжемся с вами для уточнения.\n\n"
        "❓ Вы работаете по выходным?\n"
        "— Да, мы работаем каждый день с 09:00 до 20:00."
    )
    await update.message.reply_text(text)

# async def question_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.effective_user.id
#     question = update.message.text
#     username = update.effective_user.username or "Без username"

#     # Сохраняем
#     user_questions[user_id] = question

#     # Отправка админу
#     admin_text = (
#         f"❓ Новый вопрос от @{username} (ID: {user_id}):\n\n"
#         f"{question}\n\n"
#         f"Ответить: /reply {user_id} ваш_ответ"
#     )

#     await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)
#     await update.message.reply_text("Спасибо! Ваш вопрос отправлен, скоро мы ответим.")
#     return ConversationHandler.END

# === Запуск бота ===


async def house_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_type = update.message.text
    context.user_data["house_type"] = user_type

    await update.message.reply_text(
        "Спасибо! Ваша заявка принята. Мы свяжемся с вами в ближайшее время. ✅"
    )

HOUSE_TYPE = 10



def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token("8047716790:AAF3Orl4sM7lMe6IMxHbybYcsh4aSpRhIRA").build()

    ask_conv = ConversationHandler(
        entry_points=[CommandHandler("ask", ask_question_start),
                      MessageHandler(filters.Regex("❓"), ask_question_start)],
        states={
            ASKING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, question_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    handlers = [
    CommandHandler("start", start),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
    ]

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
            HOUSE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, house_type_handler)],
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
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(ask_conv)
    app.add_handler(MessageHandler(filters.REPLY & filters.Chat(chat_id=ADMIN_CHAT_ID), forward_admin_reply))
    app.add_handler(CommandHandler("reply", reply_command))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())