"""
Telegram-бот «Тело как система» — Дмитрий
==========================================
Требования:
    pip install python-telegram-bot

Запуск:
    python telo_bot.py

Настройка (заполни перед запуском):
    BOT_TOKEN    — токен от BotFather
    ADMIN_ID     — твой Telegram user_id
    PDF_PATH     — путь к PDF-чеклисту (или None)
    CHANNEL      — ссылка на Telegram-канал
    CALENDLY_URL — ссылка для записи в Calendly
"""

import json
import urllib.request
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# ─── НАСТРОЙКИ ────────────────────────────────────────────────────────────────
BOT_TOKEN    = "8313728401:AAGr0A6BbHjzVOVbozW_d8-bXGLqhMAVuzI"
ADMIN_ID     = 485184183
PDF_PATH     = "checklist.pdf"
CHANNEL      = "https://t.me/teloofsystem"
CALENDLY_URL = "https://calendly.com/frnomad00/30min"
N8N_WEBHOOK_URL  = "https://n8n.dum35.ru/webhook/051c7e0e-d4a6-4bc5-99a7-a26987e60735"

# ─── СОСТОЯНИЯ ДИАЛОГА ────────────────────────────────────────────────────────
(
    MAIN_MENU,
    Q1_AGE,
    Q2_GOAL,
    Q3_TRAINING,
    Q4_PROBLEM,
    Q5_CONTACT,
) = range(6)

# ─── ЛОГИРОВАНИЕ ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── КЛАВИАТУРЫ ───────────────────────────────────────────────────────────────
def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Хочу чеклист", callback_data="checklist")],
        [InlineKeyboardButton("📞 Записаться на разбор", callback_data="signup")],
    ])

def kb_after_checklist():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Записаться на разбор", callback_data="signup")],
        [InlineKeyboardButton("❓ Узнать больше", callback_data="more")],
    ])

def kb_age():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("35–40", callback_data="35-40"), InlineKeyboardButton("41–47", callback_data="41-47")],
        [InlineKeyboardButton("48–55", callback_data="48-55"), InlineKeyboardButton("55+", callback_data="55+")],
    ])

def kb_goal():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Сбросить вес", callback_data="Сбросить вес")],
        [InlineKeyboardButton("Набрать мышцы", callback_data="Набрать мышцы")],
        [InlineKeyboardButton("Больше энергии", callback_data="Больше энергии")],
        [InlineKeyboardButton("Здоровье и анализы", callback_data="Здоровье и анализы")],
    ])

def kb_training():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Да, регулярно", callback_data="Да, регулярно")],
        [InlineKeyboardButton("Иногда, непостоянно", callback_data="Иногда, непостоянно")],
        [InlineKeyboardButton("Нет, давно бросил", callback_data="Нет, давно бросил")],
        [InlineKeyboardButton("Никогда не занимался", callback_data="Никогда не занимался")],
    ])

def kb_problem():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Нет времени", callback_data="Нет времени")],
        [InlineKeyboardButton("Нет мотивации", callback_data="Нет мотивации")],
        [InlineKeyboardButton("Не знаю с чего начать", callback_data="Не знаю с чего начать")],
        [InlineKeyboardButton("Мешают боли/здоровье", callback_data="Мешают боли/здоровье")],
    ])

# ─── ХЭНДЛЕРЫ ─────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "Привет! Это бот Дмитрия — тренера по мужскому здоровью.\n\n"
        "Здесь ты можешь:\n"
        "📄 Получить PDF-чеклист «5 ошибок мужчин 35+ в зале»\n"
        "📞 Записаться на бесплатный разбор здоровья\n\n"
        "Что делаем?",
        reply_markup=kb_main(),
    )
    return MAIN_MENU

async def send_checklist(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if PDF_PATH:
        await query.message.reply_document(
            document=open(PDF_PATH, "rb"),
            caption=(
                "Держи! 👇\n\n"
                "«5 ошибок мужчин 35+ в зале» — сохрани, там без воды.\n\n"
                "Если хочешь разобраться, что мешает тебе — "
                "запишись на бесплатный 20-минутный разбор."
            ),
            reply_markup=kb_after_checklist(),
        )
    else:
        await query.message.reply_text(
            "Держи! 👇\n\n"
            "📄 <b>«5 ошибок мужчин 35+ в зале»</b>\n\n"
            "1. Тренируешься без учёта восстановления\n"
            "2. Ешь «правильно», но не под свой метаболизм 35+\n"
            "3. Игнорируешь анализы — а там корень проблем\n"
            "4. Упражнения из YouTube без учёта особенностей\n"
            "5. Нет системы — есть набор хаотичных действий\n\n"
            "Запишись на бесплатный 20-минутный разбор.",
            parse_mode="HTML",
            reply_markup=kb_after_checklist(),
        )
    return MAIN_MENU

async def more_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Дмитрий — тренер по мужскому здоровью, специализация: мужчины 35+.\n\n"
        "Работает с:\n"
        "• питанием под твой метаболизм\n"
        "• тренировками с учётом суставов и гормонального фона\n"
        "• восстановлением и анализами\n\n"
        f"Канал: {CHANNEL}\n\n"
        "Разбор — 20 минут, конкретно по твоей ситуации.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Записаться", callback_data="signup")]
        ]),
    )
    return MAIN_MENU

async def start_signup(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Отлично. 5 коротких вопросов — займёт 2 минуты.\n\n"
        "<b>1/5 — Сколько тебе лет?</b>",
        parse_mode="HTML",
        reply_markup=kb_age(),
    )
    return Q1_AGE

async def q1_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["age"] = query.data
    await query.message.reply_text(
        "<b>2/5 — Какая главная цель сейчас?</b>",
        parse_mode="HTML", reply_markup=kb_goal(),
    )
    return Q2_GOAL

async def q2_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["goal"] = query.data
    await query.message.reply_text(
        "<b>3/5 — Ты сейчас тренируешься?</b>",
        parse_mode="HTML", reply_markup=kb_training(),
    )
    return Q3_TRAINING

async def q3_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["training"] = query.data
    await query.message.reply_text(
        "<b>4/5 — Что сейчас больше всего мешает?</b>",
        parse_mode="HTML", reply_markup=kb_problem(),
    )
    return Q4_PROBLEM

async def q4_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ctx.user_data["problem"] = query.data
    await query.message.reply_text(
        "<b>5/5 — Как тебя зовут и как с тобой связаться?</b>\n\n"
        "Напиши имя и телефон или Telegram-ник ✍️",
        parse_mode="HTML",
    )
    return Q5_CONTACT

async def q5_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    contact = update.message.text
    ctx.user_data["contact"] = contact
    d = ctx.user_data
    user = update.effective_user
    name = contact.split()[0] if contact else "Привет"

    await update.message.reply_text(
        f"Отлично, {name}! Всё принял 👍\n\n"
        "Дмитрий свяжется в течение нескольких часов.\n\n"
        "<b>Хочешь выбрать удобное время прямо сейчас?</b>\n\n"
        "📅 Нажми кнопку — откроется календарь, выбери слот. Займёт 30 секунд.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Выбрать время для созвона", url=CALENDLY_URL)],
        ]),
    )

    tg_link = f"tg://user?id={user.id}" if user.id else "—"
    notify = (
        "🔥 <b>НОВАЯ ЗАЯВКА — Тело как система</b>\n\n"
        f"Контакт: {contact}\n"
        f"Telegram: @{user.username or '—'} | <a href='{tg_link}'>написать</a>\n\n"
        f"Возраст: {d.get('age', '—')}\n"
        f"Цель: {d.get('goal', '—')}\n"
        f"Тренируется: {d.get('training', '—')}\n"
        f"Помеха: {d.get('problem', '—')}"
    )
    try:
        await ctx.bot.send_message(chat_id=ADMIN_ID, text=notify, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Уведомление тренеру не отправлено: {e}")

    # Send to CRM
    tg_handle = f"@{user.username}" if user.username else str(user.id)
    await send_to_crm(ctx.user_data, tg_handle)

    ctx.user_data.clear()
    return ConversationHandler.END


async def send_to_crm(data: dict, telegram: str) -> None:
    """Send questionnaire answers to n8n → Google Sheets CRM."""
    import asyncio
    from datetime import datetime
    payload = json.dumps({
        "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Имя/Контакт": data.get("contact", ""),
        "Telegram": telegram,
        "Возраст": data.get("age", ""),
        "Цель": data.get("goal", ""),
        "Тренируется": data.get("training", ""),
        "Помеха": data.get("problem", ""),
        "Источник": "Бот",
        "Этап": "Заявка",
        "Статус": "Новый",
    }, ensure_ascii=False).encode("utf-8")

    def _post():
        req = urllib.request.Request(
            N8N_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        urllib.request.urlopen(req, timeout=10)

    try:
        await asyncio.to_thread(_post)
        logger.info("CRM: данные отправлены в n8n")
    except Exception as e:
        logger.warning(f"CRM webhook error: {e}")

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Окей, если надумаешь — напиши /start")
    ctx.user_data.clear()
    return ConversationHandler.END

async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши /start чтобы начать 👇")

# ─── ЗАПУСК ───────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_signup, pattern="^signup$"),
        ],
        states={
            MAIN_MENU:   [
                CallbackQueryHandler(send_checklist, pattern="^checklist$"),
                CallbackQueryHandler(start_signup, pattern="^signup$"),
                CallbackQueryHandler(more_info, pattern="^more$"),
            ],
            Q1_AGE:      [CallbackQueryHandler(q1_answer)],
            Q2_GOAL:     [CallbackQueryHandler(q2_answer)],
            Q3_TRAINING: [CallbackQueryHandler(q3_answer)],
            Q4_PROBLEM:  [CallbackQueryHandler(q4_answer)],
            Q5_CONTACT:  [MessageHandler(filters.TEXT & ~filters.COMMAND, q5_contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    logger.info("Бот запущен.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
