import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# قراءة المفاتيح من متغيرات البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

# التحقق من وجود القيم
if not BOT_TOKEN or not OPENROUTER_KEY:
    raise ValueError("❌ تأكد من إضافة BOT_TOKEN و OPENROUTER_KEY في Environment Variables على Deta Space.")

async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الرد على الرسائل النصية باستخدام OpenRouter API"""
    user_message = update.message.text

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://example.com",  # يمكنك تغييره
        "X-Title": "Telegram AI Bot"
    }
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": user_message}]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        reply_text = data.get("choices", [{}])[0].get("message", {}).get("content", "⚠️ لم أتمكن من جلب رد.")
    except requests.exceptions.RequestException as e:
        reply_text = f"⚠️ خطأ في الاتصال: {e}"
    except Exception as e:
        reply_text = f"⚠️ خطأ غير متوقع: {e}"

    await update.message.reply_text(reply_text)

def main():
    """تشغيل البوت"""
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
    app.run_polling()

if __name__ == "__main__":
    main()
