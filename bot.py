import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    CommandHandler
)

# قراءة المفاتيح من Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # رابط الخدمة على Render

if not BOT_TOKEN or not OPENROUTER_KEY or not WEBHOOK_URL:
    raise ValueError("❌ تأكد من إضافة BOT_TOKEN و OPENROUTER_KEY و WEBHOOK_URL في Environment Variables.")

# ------------------------
# تسجيل المحادثات
# ------------------------
def log_message(user, message, reply):
    with open("chat_log.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {user}: {message}\n[Bot]: {reply}\n\n")

# ------------------------
# أوامر /start و /help
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحبًا بك في خدمة العملاء! 🛎\n"
        "أرسل أي سؤال وسأرد عليك مباشرة.\n"
        "يمكنك استخدام /help لمعرفة المزيد."
    )
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📌 تعليمات استخدام البوت:\n"
        "- أرسل أي استفسار أو شكوى أو ملاحظة.\n"
        "- سأحاول الرد عليك مباشرة باستخدام AI.\n"
        "- استخدم /start لإعادة الترحيب.\n"
        "- سيتم تسجيل المحادثات لتحسين الخدمة."
    )
    await update.message.reply_text(help_text)

# ------------------------
# الرد الذكي على الرسائل
# ------------------------
async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_name = update.message.from_user.username or update.message.from_user.first_name

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://example.com",
        "X-Title": "Telegram Customer Service Bot"
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
        reply_text = f"⚠️ خطأ في الاتصال بالخادم: {e}"
    except Exception as e:
        reply_text = f"⚠️ خطأ غير متوقع: {e}"

    await update.message.reply_text(reply_text)

    # تسجيل الرسائل
    log_message(user_name, user_message, reply_text)

# ------------------------
# تشغيل البوت باستخدام Webhook
# ------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # إضافة أوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # الرد على الرسائل النصية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))

    # Webhook setup
    port = int(os.environ.get("PORT", 5000))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=WEBHOOK_URL
    )
    print("✅ Bot running with Webhook")

if __name__ == "__main__":
    main()
