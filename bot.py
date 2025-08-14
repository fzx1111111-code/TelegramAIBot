import os
import logging
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
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
PORT = int(os.environ.get('PORT', 8000))

# التحقق من وجود المتغيرات البيئية
required_vars = {
    "BOT_TOKEN": BOT_TOKEN,
    "OPENROUTER_KEY": OPENROUTER_KEY,
    "WEBHOOK_URL": WEBHOOK_URL
}

for name, value in required_vars.items():
    if not value:
        logger.error(f"❌ {name} غير موجود")
        exit(1)

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
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "📌 تعليمات:\n"
            "- أرسل أي استفسار، شكوى، أو اقتراح.\n"
            "- سأرد عليك مباشرة باستخدام الذكاء الاصطناعي.\n"
            "- سيتم تسجيل المحادثات لتحسين الخدمة."
        )
    except Exception as e:
        logger.error(f"Error in help command: {e}")

# ------------------------
# الرد الذكي على الرسائل
# ------------------------
async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_message = update.message.text
        user = update.message.from_user
        user_name = user.username or user.first_name or "Unknown"
        
        logger.info(f"Received message from {user_name}: {user_message}")
        
        # إرسال رسالة انتظار
        waiting_message = await update.message.reply_text("⏳ جاري الرد...")
        
        # إعداد طلب API
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
        try:
            await waiting_message.delete()
        except Exception as e:
            logger.warning(f"Couldn't delete waiting message: {e}")
            
        await update.message.reply_text(reply_text)
        log_message(user_name, user_message, reply_text)
        
    except Exception as e:
        logger.error(f"Error in ai_reply: {e}")
        try:
            await update.message.reply_text("⚠️ عذراً، حدث خطأ أثناء معالجة رسالتك.")
        except Exception:
            logger.error("Failed to send error message")

# ------------------------
# معالجة الأخطاء العامة
# ------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error: {context.error}", exc_info=context.error)

# ------------------------
# الدالة الرئيسية
# ------------------------
def main() -> None:
    try:
        logger.info("🚀 بدء تشغيل البوت...")
        
        # إنشاء التطبيق
        application = Application.builder().token(BOT_TOKEN).build()
        
        # إضافة المعالجات
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
        application.add_error_handler(error_handler)
        
        # إعداد الـ webhook
        logger.info(f"Setting webhook to: {WEBHOOK_URL}")
        
        # التعديل الرئيسي هنا: استخدام طريقة مختلفة لتشغيل Webhook
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}")
        
        # تشغيل التطبيق
        application.run_polling(
            host='0.0.0.0',
            port=PORT,
            webhook_url=WEBHOOK_URL
        )
        
        logger.info("✅ Bot is running with webhook!")
        
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        exit(1)

if __name__ == "__main__":
    main()
