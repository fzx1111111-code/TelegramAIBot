import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل أي رسالة، وسأرد عليك.")

async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم استلام رسالتك!")

async def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))

    while True:
        try:
            print("✅ Bot started polling")
            await app.run_polling()
        except Exception as e:
            print(f"⚠️ حدث خطأ: {e}")
            await asyncio.sleep(5)  # إعادة المحاولة بعد 5 ثواني

if __name__ == "__main__":
    asyncio.run(run_bot())
