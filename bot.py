#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import requests
import asyncio
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
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# قراءة المتغيرات
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8000))

# فحص المتغيرات
logger.info("🔍 فحص المتغيرات...")
logger.info(f"BOT_TOKEN: {'✅ موجود' if BOT_TOKEN else '❌ مفقود'}")
logger.info(f"OPENROUTER_KEY: {'✅ موجود' if OPENROUTER_KEY else '❌ مفقود'}")
logger.info(f"WEBHOOK_URL: {'✅ موجود' if WEBHOOK_URL else '❌ مفقود'}")
logger.info(f"PORT: {PORT}")

if not all([BOT_TOKEN, OPENROUTER_KEY, WEBHOOK_URL]):
    logger.error("❌ بعض المتغيرات مفقودة")
    sys.exit(1)

# ------------------------
# المعالجات
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /start"""
    try:
        await update.message.reply_text(
            "🤖 مرحبًا! أنا بوت خدمة العملاء\n"
            "أرسل لي أي رسالة وسأرد عليك!\n"
            "استخدم /help للمساعدة"
        )
        logger.info(f"Start command من المستخدم: {update.effective_user.first_name}")
    except Exception as e:
        logger.error(f"خطأ في start: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر /help"""
    try:
        await update.message.reply_text(
            "📋 الأوامر المتاحة:\n"
            "/start - بدء المحادثة\n"
            "/help - عرض المساعدة\n\n"
            "💬 أرسل أي رسالة نصية وسأرد عليك باستخدام الذكاء الاصطناعي"
        )
        logger.info(f"Help command من المستخدم: {update.effective_user.first_name}")
    except Exception as e:
        logger.error(f"خطأ في help: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الرسائل النصية"""
    try:
        user_message = update.message.text
        user_name = update.effective_user.first_name or "مستخدم"
        
        logger.info(f"📨 رسالة من {user_name}: {user_message[:50]}...")
        
        # رسالة انتظار
        status_msg = await update.message.reply_text("⏳ جاري المعالجة...")
        
        # استدعاء AI
        ai_response = await get_ai_response(user_message)
        
        # حذف رسالة الانتظار وإرسال الرد
        await status_msg.delete()
        await update.message.reply_text(ai_response)
        
        logger.info(f"✅ تم الرد على {user_name}")
        
    except Exception as e:
        logger.error(f"خطأ في معالجة الرسالة: {e}")
        try:
            await update.message.reply_text("❌ عذراً، حدث خطأ في المعالجة")
        except:
            pass

async def get_ai_response(message: str) -> str:
    """الحصول على رد من AI"""
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": WEBHOOK_URL,
            "X-Title": "Telegram Bot"
        }
        
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": "أنت مساعد ذكي. أجب باللغة العربية بشكل مفيد ومهذب."},
                {"role": "user", "content": message}
            ],
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        # استخدام asyncio لعدم حجب التطبيق
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: requests.post(url, headers=headers, json=payload, timeout=30)
        )
        
        response.raise_for_status()
        data = response.json()
        
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
        else:
            return "⚠️ لم أتمكن من الرد، حاول مرة أخرى"
            
    except Exception as e:
        logger.error(f"خطأ في AI API: {e}")
        return "⚠️ عذراً، هناك مشكلة مؤقتة في الخدمة"

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء العام"""
    logger.error(f"خطأ: {context.error}")

# ------------------------
# الدالة الرئيسية
# ------------------------
def main():
    """تشغيل البوت"""
    try:
        logger.info("🚀 بدء تشغيل البوت...")
        
        # إنشاء التطبيق
        app = Application.builder().token(BOT_TOKEN).build()
        
        # إضافة المعالجات
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_error_handler(error_handler)
        
        logger.info(f"🌐 تشغيل الـ webhook على البورت {PORT}")
        logger.info(f"🔗 رابط الـ webhook: {WEBHOOK_URL}")
        
        # تشغيل الـ webhook
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="",
            webhook_url=WEBHOOK_URL
        )
        
    except Exception as e:
        logger.error(f"❌ فشل في تشغيل البوت: {e}")
        sys.exit(1)

# نقطة البداية
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"💥 خطأ فادح: {e}")
        sys.exit(1)
