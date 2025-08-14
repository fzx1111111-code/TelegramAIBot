import os
import sys
import asyncio
import logging
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

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قراءة المفاتيح من Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

print(f"BOT_TOKEN exists: {bool(BOT_TOKEN)}")
print(f"OPENROUTER_KEY exists: {bool(OPENROUTER_KEY)}")
print(f"WEBHOOK_URL exists: {bool(WEBHOOK_URL)}")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN غير موجود")
    sys.exit(1)
if not OPENROUTER_KEY:
    logger.error("❌ OPENROUTER_KEY غير موجود")
    sys.exit(1)
if not WEBHOOK_URL:
    logger.error("❌ WEBHOOK_URL غير موجود")
    sys.exit(1)

# ------------------------
# تسجيل المحادثات
# ------------------------
def log_message(user, message, reply):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {user}: {message}\n[Bot]: {reply}\n\n"
        print(log_entry)
    except Exception as e:
        logger.error(f"Error logging message: {e}")

# ------------------------
# أوامر /start و /help
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "مرحبًا بك في خدمة العملاء! 🛎\n"
            "أرسل أي سؤال وسأرد عليك مباشرة.\n"
            "استخدم /help لمعرفة المزيد."
        )
        logger.info("Start command executed successfully")
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "📌 تعليمات:\n"
            "- أرسل أي استفسار، شكوى، أو اقتراح.\n"
            "- سأرد عليك مباشرة باستخدام AI.\n"
            "- سيتم تسجيل المحادثات لتحسين الخدمة."
        )
        logger.info("Help command executed successfully")
    except Exception as e:
        logger.error(f"Error in help command: {e}")

# ------------------------
# الرد الذكي على الرسائل
# ------------------------
async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        user_name = update.message.from_user.username or update.message.from_user.first_name or "Unknown"
        
        logger.info(f"Received message from {user_name}: {user_message}")
        
        # إرسال رسالة انتظار
        waiting_message = await update.message.reply_text("⏳ جاري الرد...")
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "HTTP-Referer": WEBHOOK_URL,
            "X-Title": "Telegram Customer Service Bot",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {
                    "role": "system", 
                    "content": "أنت مساعد ذكي لخدمة العملاء. أجب باللغة العربية بشكل مهذب ومفيد."
                },
                {
                    "role": "user", 
                    "content": user_message
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                reply_text = data["choices"][0]["message"]["content"]
            else:
                reply_text = "⚠️ عذراً، لم أتمكن من الرد على استفسارك. يرجى المحاولة مرة أخرى."
                
        except requests.RequestException as e:
            logger.error(f"API Request Error: {e}")
            reply_text = "⚠️ عذراً، هناك مشكلة تقنية. يرجى المحاولة لاحقاً."
        except Exception as e:
            logger.error(f"Unexpected API Error: {e}")
            reply_text = "⚠️ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
        
        # حذف رسالة الانتظار وإرسال الرد
        await waiting_message.delete()
        await update.message.reply_text(reply_text)
        
        log_message(user_name, user_message, reply_text)
        logger.info(f"Reply sent successfully to {user_name}")
        
    except Exception as e:
        logger.error(f"Error in ai_reply: {e}")
        try:
            await update.message.reply_text("⚠️ عذراً، حدث خطأ أثناء معالجة رسالتك.")
        except:
            pass

# ------------------------
# معالجة الأخطاء العامة
# ------------------------
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

# ------------------------
# تشغيل البوت باستخدام Webhook
# ------------------------
async def main():
    try:
        logger.info("🚀 بدء تشغيل البوت...")
        
        # بناء التطبيق
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # إضافة المعالجات
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
        application.add_error_handler(error_handler)
        
        # إعداد الـ webhook
        port = int(os.environ.get("PORT", 8000))
        webhook_path = f"/webhook/{BOT_TOKEN}"
        webhook_url = f"{WEBHOOK_URL.rstrip('/')}{webhook_path}"
        
        logger.info(f"Webhook URL: {webhook_url}")
        logger.info(f"Port: {port}")
        
        # تشغيل الـ webhook
        await application.bot.set_webhook(url=webhook_url)
        logger.info("✅ Webhook تم إعداده بنجاح")
        
        # بدء الخدمة
        await application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_path,
            webhook_url=webhook_url
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # تشغيل الحدث الرئيسي
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
