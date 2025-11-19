from db import add_reps, init_db, get_user_stats_today, get_group_stats_today, get_user_stats_period, get_group_stats_period, get_challenge_status, get_display_name
from config import BOT_TOKEN
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from config import CHALLENGE_START
from datetime import datetime
import re

# /start
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в челлендж по отжиманиям!\n"
        "Можешь просто писать в чат что-то типа: отжался 20\n"
        "Или использовать команду /setreps 20"
    )

# /setreps <число>
async def setreps_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        reps = int(context.args[0])
        user = update.effective_user
        reps_done, completed = add_reps(
            user.id,
            user.username or "",
            user.full_name or "",
            reps
        )
        response = f"@{user.username}, у тебя {reps_done}/100 за сегодня."
        if completed:
            response += " Молодец, дневная норма закрыта!"
        await update.message.reply_text(response)
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Используй как:\n/setreps <количество>\nНапример: /setreps 20"
        )

# Обработка обычных сообщений вида "отжался 20"
async def reps_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    match = re.search(r'отжал[а-яё]*\s*:?[\s]*(\d+)', text)
    if match:
        reps = int(match.group(1))
        user = update.effective_user
        reps_done, completed = add_reps(
            user.id,
            user.username or "",
            user.full_name or "",
            reps
        )
        response = (
            f"@{user.username}, у тебя {reps_done}/100 за сегодня."
            + (" Молодец, дневная норма закрыта!" if completed else "")
        )
        await update.message.reply_text(response)

# /today
async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reps_done, completed = get_user_stats_today(user.id)
    response = f"Сегодня ты сделал {reps_done}/100 отжиманий."
    if completed:
        response += " Дневная норма выполнена!"
    else:
        response += f" Осталось {100 - reps_done}."
    await update.message.reply_text(response)

# /stats
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_group_stats_today()
    response = "Статистика по дням:\n"
    for username, full_name, custom_name, reps_done, completed in rows:
        reps_shown = reps_done if reps_done is not None else 0
        done_str = "✅" if completed else "❌"
        display_name = get_display_name(username, full_name, custom_name)
        response += f"{display_name}: {reps_shown}/100 {done_str}\n"
    await update.message.reply_text(response)

# /total
async def total_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    today = datetime.now().strftime("%Y-%m-%d")
    total = get_user_stats_period(user.id, CHALLENGE_START, today)
    response = f"С {CHALLENGE_START} по сегодня ты сделал {total} отжиманий!"
    await update.message.reply_text(response)

# /teamtotal
async def teamtotal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%Y-%m-%d")
    rows = get_group_stats_period(CHALLENGE_START, today)
    response = f"🏆 С {CHALLENGE_START} по сегодня:\n"
    for username, full_name, custom_name, total_done in rows:
        total_shown = total_done if total_done is not None else 0
        display_name = get_display_name(username, full_name, custom_name)
        response += f"{display_name}: {total_shown} отжиманий\n"
    await update.message.reply_text(response)

# /challenge
async def challenge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = get_challenge_status()
    msg = (
        f"🏆 <b>Статус челленджа</b>\n"
        f"Всего дней: <b>{status['days_total']}</b>\n"
        f"Прошло дней: <b>{status['days_passed']}</b>\n"
        f"Осталось дней: <b>{status['days_left']}</b>\n"
        f"Финиш: <b>{status['date_end']}</b>\n\n"
        f"Суммарно отжиманий: <b>{status['total_reps']}</b>\n"
        f"План на сегодня: <b>{status['plan_reps']}</b>\n"
        f"Выполнено команды: <b>{status['percent']}%</b>\n"
    )
    # Используй display_name для каждого "идеального" участника
    if status['perfect_users']:
        users = ', '.join([
            get_display_name(username, full_name, custom_name)
            for username, full_name, custom_name in status['perfect_users']
        ])
        msg += f"\n💯 Всегда выполняли норму: {users}"
    await update.message.reply_text(msg, parse_mode="HTML")

if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("challenge", challenge_handler))
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("total", total_handler))
    app.add_handler(CommandHandler("teamtotal", teamtotal_handler))
    app.add_handler(CommandHandler("setreps", setreps_handler))
    app.add_handler(CommandHandler("today", today_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reps_message_handler))
    print("Бот запущен. Чтобы остановить — нажми Ctrl+C.")
    app.run_polling()
