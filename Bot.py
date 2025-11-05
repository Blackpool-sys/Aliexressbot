import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# التوكن من متغير البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found!")
    exit(1)

# أوامر البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البدء"""
    try:
        welcome_text = """
🎯 **مرحباً بك في بوت العروض الحصرية!**

✅ **الأوامر المتاحة:**
/start - بدء الاستخدام
/hot - أفضل العروض الساخنة 🏆
/عروض - العروض المميزة اليومية  
/help - المساعدة
/test - اختبار البوت

🔥 **احصل على أفضل العروض من AliExpress بخصومات حقيقية!**
        """
        await update.message.reply_text(welcome_text)
        logger.info(f"✅ Start command from user {update.effective_chat.id}")
    except Exception as e:
        logger.error(f"❌ Start error: {e}")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختبار البوت"""
    try:
        user = update.effective_user
        response = f"""
✅ **البوت يعمل بشكل ممتاز!**

👤 **المستخدم:** {user.first_name}
🆔 **الرقم:** {update.effective_chat.id}
🚀 **الحالة:** نشط ومستعد

🎯 **جرب /hot لرؤية العروض الساخنة!**
        """
        await update.message.reply_text(response)
        logger.info(f"✅ Test command from user {update.effective_chat.id}")
    except Exception as e:
        logger.error(f"❌ Test error: {e}")

async def hot_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العروض الساخنة"""
    try:
        chat_id = update.effective_chat.id
        logger.info(f"🔥 Hot offers command from user {chat_id}")
        
        # رسالة انتظار
        wait_msg = await update.message.reply_text("🔍 **جاري البحث عن أفضل العروض الساخنة...**")
        
        # عروض تجريبية (سيتم استبدالها بـ API حقيقي)
        sample_offers = [
            {
                'title': 'سماعات بلوتوث لاسلكية مع شحن',
                'price': '$15.99',
                'discount': '60%',
                'original_price': '$39.99',
                'rating': '4.5/5',
                'sales': '2.4K'
            },
            {
                'title': 'شاحن سريع 45W مع كابل Type-C',
                'price': '$8.99', 
                'discount': '55%',
                'original_price': '$19.99',
                'rating': '4.3/5',
                'sales': '1.8K'
            },
            {
                'title': 'ساعة ذكية تتبع الصحة واللياقة',
                'price': '$25.99',
                'discount': '50%', 
                'original_price': '$51.99',
                'rating': '4.6/5',
                'sales': '3.2K'
            }
        ]
        
        # إرسال رسالة النتائج
        await wait_msg.edit_text(f"🎯 **تم العثور على {len(sample_offers)} عرض ساخن**\n\n**أفضل العروض اليوم:** 👇")
        
        # إرسال العروض
        for i, offer in enumerate(sample_offers, 1):
            offer_text = f"""
🔥 **العرض #{i}**

🏷 **{offer['title']}**

💰 **السعر:** {offer['price']} ~~{offer['original_price']}~~
📉 **الخصم:** {offer['discount']}
⭐ **التقييم:** {offer['rating']}
🛒 **المبيعات:** {offer['sales']}

⚡ **عرض محدود - اسرع قبل النفاد!**
            """
            await update.message.reply_text(offer_text)
            
        logger.info(f"✅ Sent {len(sample_offers)} offers to user {chat_id}")
        
    except Exception as e:
        logger.error(f"❌ Hot offers error: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء جلب العروض. جرب مرة أخرى لاحقاً.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المساعدة"""
    try:
        help_text = """
🆘 **مساعدة البوت**

🎯 **كيف تحصل على أفضل العروض؟**
1. استخدم /hot للعروض الساخنة
2. استخدم /عروض للعروض اليومية
3. تابع البوت يومياً

🔥 **مميزات البوت:**
• عروض بخصومات حقيقية
• منتجات عالية التقييم  
• عروض محدودة الوقت
• روابط شراء مباشرة

⚡ **الأوامر:**
/start - بدء الاستخدام
/hot - العروض الساخنة
/عروض - عروض اليوم
/test - اختبار البوت
/help - المساعدة
        """
        await update.message.reply_text(help_text)
        logger.info(f"✅ Help command from user {update.effective_chat.id}")
    except Exception as e:
        logger.error(f"❌ Help error: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية"""
    try:
        user = update.effective_user
        await update.message.reply_text(f"🤖 **مرحباً {user.first_name}!**\n\nاستخدم /help لرؤية الأوامر المتاحة")
    except Exception as e:
        logger.error(f"❌ Message handling error: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    logger.error(f"❌ Error occurred: {context.error}")

def main():
    """الدالة الرئيسية"""
    try:
        logger.info("🚀 Starting bot application...")
        
        # إنشاء التطبيق
        application = Application.builder().token(BOT_TOKEN).build()
        
        # إضافة المعالجات
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("test", test))
        application.add_handler(CommandHandler("hot", hot_offers))
        application.add_handler(CommandHandler("عروض", hot_offers))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # معالج الأخطاء
        application.add_error_handler(error_handler)
        
        # بدء البوت
        logger.info("🤖 Bot is now running...")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🎯 ALIEXPRESS BOT - OFFICIAL TELEGRAM LIBRARY")
    logger.info("=" * 50)
    main()
