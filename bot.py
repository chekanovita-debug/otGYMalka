from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from db import add_reps, init_db      # Не забудь скопировать add_reps из примеров выше!
from config import BOT_TOKEN

# Обработчик команды /start
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в челлендж по отжиманиям!\n"
        "Используй /setreps <кол-во>, чтобы записать свои отжимания.\n"
        "Например: /setreps 20"
    )

# Обработчик команды /setreps <число>
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
        await update.message.reply_text("Используй как:\n/setreps <количество>\nНапример: /setreps 20")

if __name__ == "__main__":
    init_db()  # На всякий случай
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("setreps", setreps_handler))
    print("Бот запущен. Чтобы остановить — нажми Ctrl+C.")
    app.run_polling()
