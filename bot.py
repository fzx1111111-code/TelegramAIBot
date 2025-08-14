from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import requests

# مفاتيحك
BOT_TOKEN = "8253319257:AAGL80rYjabVhCWhwYsXbhZWfvcz-VhFtfc"
OPENROUTER_KEY = "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"

async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://example.com",  # تقدر تغيّره لرابطك
        "X-Title": "Telegram AI Bot"
    }
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": user_message}]
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        reply_text = res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply_text = f"حدث خطأ في الاتصال: {str(e)}"

    await update.message.reply_text(reply_text)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
app.run_polling()
