"""
Telegram-бот «Тело как система» — Дмитрий
==========================================
v2 — сегментация + оплата через СБП
"""

import json
import os
import urllib.request
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters, ContextTypes,
)

BOT_TOKEN     = "8313728401:AAGr0A6BbHjzVOVbozW_d8-bXGLqhMAVuzI"
ADMIN_ID      = 485184183
PDF_PATH      = "checklist.pdf"
CHANNEL       = "https://t.me/teloofsystem"
CALENDLY_URL  = "https://calendly.com/frnomad00/30min"
N8N_WEBHOOK   = "https://n8n.dum35.ru/webhook/051c7e0e-d4a6-4bc5-99a7-a26987e60735"
PAYMENT_PHONE = os.environ.get("PAYMENT_PHONE", "")

(MAIN_MENU, Q1_AGE, Q2_GOAL, Q3_TRAINING, Q4_PROBLEM, Q5_CONTACT) = range(6)

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

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
        [InlineKeyboardButton("Пробовал — не работало", callback_data="Пробовал — не работало")],
    ])

def kb_calendly():
    phone_digits = PAYMENT_PHONE.replace("+", "").replace(" ", "")
    payment_url = f"https://www.tinkoff.ru/rm/transfer/{phone_digits}?comment=Razzbor+zdorovya"
    buttons = [[InlineKeyboardButton("📅 Выбрать время для созвона", url=CALENDLY_URL)]]
    if PAYMENT_PHONE:
        buttons.append([InlineKeyboardButton("💳 Оплатить разбор — 5 000 ₽", url=payment_url)])
    return InlineKeyboardMarkup(buttons)


def get_final_message(name, goal, problem):
    suffix = "\n\n📅 Выбери время в календаре — и оплати разбор, чтобы подтвердить бронь."
    if goal == "Сбросить вес":
        return (f"{name}, принял! 👍\n\n"
            "После 35 вес уходит по другим правилам — не через голодовку и кардио, "
            "а через работу с метаболизмом, гормонами и инсулином.\n\n"
            "На разборе посмотрю твою ситуацию конкретно: что блокирует результат "
            "и 3–5 шагов, которые реально сдвинут цифры на весах.\n\n"
            "<b>Дмитрий свяжется с тобой в течение нескольких часов.</b>" + suffix)
    elif goal == "Набрать мышцы":
        return (f"{name}, принял! 👍\n\n"
            "После 35 мышцы строятся иначе: восстановление занимает дольше, "
            "тестостерон и гормон роста уже не те. Больше тренировок — не всегда лучше.\n\n"
            "На разборе разберём нагрузку, питание и восстановление под твой возраст "
            "и уровень — чтобы прогресс шёл без плато и травм.\n\n"
            "<b>Дмитрий свяжется с тобой в течение нескольких часов.</b>" + suffix)
    elif goal == "Больше энергии":
        return (f"{name}, принял! 👍\n\n"
            "«Вечером пусто, утром тяжело» — это не возраст и не лень. "
            "Обычно за этим стоят дефициты, гормональный фон или хронический стресс.\n\n"
            "На разборе найдём корень: посмотрим анализы или объясню, что сдать, "
            "и дам конкретный план как вернуть стабильную энергию.\n\n"
            "<b>Дмитрий свяжется с тобой в течение нескольких часов.</b>" + suffix)
    elif goal == "Здоровье и анализы":
        return (f"{name}, принял! 👍\n\n"
            "Анализы — это карта, по которой понятно что происходит внутри. "
            "Большинство мужчин сдают их когда уже что-то болит. Ты думаешь вперёд — это правильно.\n\n"
            "На разборе разберём твои результаты или составим список что сдать, "
            "объясню что значат цифры и на что обратить внимание в первую очередь.\n\n"
            "<b>Дмитрий свяжется с тобой в течение нескольких часов.</b>" + suffix)
    else:
        return (f"Отлично, {name}! Всё принял 👍\n\n"
            "Дмитрий свяжется с тобой в течение нескольких часов.\n\n"
            "📅 Выбери удобное время в календаре.\n"
            "💳 После записи — оплати разбор, чтобы подтвердить бронь.")


async def start(update, ctx):
    await update.message.reply_text(
        "Привет! Я бот проекта <b>«Тело как Система»</b> — Дмитрий.\n\n"
        "Помогаю мужчинам 35+ разобраться со здоровьем: вес, энергия, тренировки — "
        "через анализы и систему, без лишнего.\n\nЧто хочешь?",
        parse_mode="HTML", reply_markup=kb_main())
    return MAIN_MENU

async def send_checklist(update, ctx):
    query = update.callback_query
    await query.answer()
    if PDF_PATH and os.path.exists(PDF_PATH):
        await query.message.reply_document(document=open(PDF_PATH, "rb"),
            caption="«5 ошибок мужчин 35+ в зале» — сохрани, там без воды.\n\nЗапишись на бесплатный разбор.",
            reply_markup=kb_after_checklist())
    else:
        await query.message.reply_text(
            "Держи! 👇\n\n📄 <b>«5 ошибок мужчин 35+ в зале»</b>\n\n"
            "1. Тренируешься без учёта восстановления\n"
            "2. Ешь «правильно», но не под свой метаболизм 35+\n"
            "3. Игнорируешь анализы — а там корень проблем\n"
            "4. Упражнения из YouTube без учёта особенностей\n"
            "5. Нет системы — есть набор хаотичных действий\n\n"
            "Запишись на бесплатный 20-минутный разбор.",
            parse_mode="HTML", reply_markup=kb_after_checklist())
    return MAIN_MENU

async def more_info(update, ctx):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Я работаю с мужчинами 35+ у которых накопилось — вес, усталость, ощущение что тело уже не то.\n\n"
        "Разбираю здоровье как систему: анализы → питание → тренировки → нутрицевтика.\n\n"
        f"Канал: {CHANNEL}\n\nРазбор — 20 минут, конкретно по твоей ситуации.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Записаться", callback_data="signup")]]))
    return MAIN_MENU

async def start_signup(update, ctx):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Отлично. 5 коротких вопросов — займёт 2 минуты.\n\n<b>1/5 — Сколько тебе лет?</b>",
        parse_mode="HTML", reply_markup=kb_age())
    return Q1_AGE

async def q1_answer(update, ctx):
    q = update.callback_query; await q.answer()
    ctx.user_data["age"] = q.data
    await q.message.reply_text("<b>2/5 — Какая главная цель сейчас?</b>", parse_mode="HTML", reply_markup=kb_goal())
    return Q2_GOAL

async def q2_answer(update, ctx):
    q = update.callback_query; await q.answer()
    ctx.user_data["goal"] = q.data
    await q.message.reply_text("<b>3/5 — Сейчас тренируешься?</b>", parse_mode="HTML", reply_markup=kb_training())
    return Q3_TRAINING

async def q3_answer(update, ctx):
    q = update.callback_query; await q.answer()
    ctx.user_data["training"] = q.data
    await q.message.reply_text("<b>4/5 — Что больше всего мешает заниматься здоровьем?</b>", parse_mode="HTML", reply_markup=kb_problem())
    return Q4_PROBLEM

async def q4_answer(update, ctx):
    q = update.callback_query; await q.answer()
    ctx.user_data["problem"] = q.data
    await q.message.reply_text("<b>5/5 — Как тебя зовут и как с тобой связаться?</b>\n\nНапиши имя и телефон или Telegram-ник ✍️", parse_mode="HTML")
    return Q5_CONTACT

async def q5_contact(update, ctx):
    contact = update.message.text
    ctx.user_data["contact"] = contact
    d = ctx.user_data
    user = update.effective_user
    name = contact.split()[0] if contact else "Привет"
    goal = d.get("goal", "")
    problem = d.get("problem", "")

    await update.message.reply_text(get_final_message(name, goal, problem),
        parse_mode="HTML", reply_markup=kb_calendly())

    tg_link = f"tg://user?id={user.id}" if user.id else "—"
    notify = (
        "🔥 <b>НОВАЯ ЗАЯВКА — Тело как система</b>\n\n"
        f"Контакт: {contact}\n"
        f"Telegram: @{user.username or '—'} | <a href='{tg_link}'>написать</a>\n\n"
        f"Возраст: {d.get('age', '—')}\nЦель: {goal or '—'}\n"
        f"Тренируется: {d.get('training', '—')}\nПомеха: {problem or '—'}"
    )
    try:
        await ctx.bot.send_message(chat_id=ADMIN_ID, text=notify, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Уведомление тренеру не отправлено: {e}")

    from datetime import datetime
    tg_handle = f"@{user.username}" if user.username else f"id:{user.id}"
    crm_payload = json.dumps({
        "Дата": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Имя/Контакт": contact, "Возраст": d.get("age", ""),
        "Цель": goal, "Опыт тренировок": d.get("training", ""),
        "Питание": "", "Восстановление": "", "Боли/Ограничения": "",
        "Мотивация": problem, "Готовность": "", "Telegram": tg_handle,
    }).encode("utf-8")
    try:
        req = urllib.request.Request(N8N_WEBHOOK, data=crm_payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        logger.warning(f"CRM webhook не сработал: {e}")
    return MAIN_MENU

async def cancel(update, ctx):
    await update.message.reply_text("Окей, если что — /start.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(send_checklist, pattern="^checklist$"),
                CallbackQueryHandler(more_info, pattern="^more$"),
                CallbackQueryHandler(start_signup, pattern="^signup$"),
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
    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
