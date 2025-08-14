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
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # رابط HTTPS الخاص بخدمة Render

if not BOT_TOKEN or not OPENROUTER_KEY or not WEBHOOK_URL:
    raise ValueError("❌ تأكد من إضافة BOT_TOKEN و OPENROUTER_KEY و WEBHOOK_URL في Environment Variables.")

# ------------------------
# تسجيل المحادثات
# ------------------------
def log_message(user, message, reply):
    try:
        with open("chat_log.txt", "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {user}: {message}\n[Bot]: {reply}\n\n")
    except Exception as e:
        print(f"Error logging message: {e}")

# ------------------------
# أوامر /start و /help
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحبًا بك في خدمة العملاء! 🛎\n"
        "أرسل أي سؤال وسأرد عليك مباشرة.\n"
        "استخدم /help لمعرفة المزيد."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 تعليمات:\n"
        "- أرسل أي استفسار، شكوى، أو اقتراح.\n"
        "- سأرد عليك مباشرة باستخدام AI.\n"
        "- سيتم تسجيل المحادثات لتحسين الخدمة."
    )

# ------------------------
# الرد الذكي على الرسائل
# ------------------------
async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_name = update.message.from_user.username or update.message.from_user.first_name
    
    print(f"Received message from {user_name}: {user_message}")
    
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
        reply_text = data.get("choices", [{}])[0].get("message", {}).get("content", "⚠️ لم أتمكن من الرد.")
    except requests.RequestException as e:
        reply_text = f"⚠️ خطأ في الاتصال بخدمة AI: {str(e)}"
        print(f"API Error: {e}")
    except Exception as e:
        reply_text = f"⚠️ حدث خطأ غير متوقع: {str(e)}"
        print(f"Unexpected Error: {e}")
    
    await update.message.reply_text(reply_text)
    log_message(user_name, user_message, reply_text)
    print(f"Sent reply: {reply_text}")

# ------------------------
# معالجة الأخطاء العامة
# ------------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

# ------------------------
# تشغيل البوت باستخدام Webhook
# ------------------------
def main():
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # إضافة أوامر
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        
        # الرد على الرسائل النصية
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
        
        # إضافة معالج الأخطاء
        app.add_error_handler(error_handler)
        
        # Webhook setup
        port = int(os.environ.get("PORT", 5000))
        
        print(f"Starting webhook on port {port} with URL: {WEBHOOK_URL}")
        
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=WEBHOOK_URL,
            url_path=""  # إضافة هذا المعامل
        )
        
        print("✅ Bot running with Webhook")
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        raise

if __name__ == "__main__":
    main()
