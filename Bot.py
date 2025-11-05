import os
import logging
import time
import telebot
from api import advanced_api
from product_filter import product_filter

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# التحقق من المكتبات
try:
    logger.info("✅ Checking dependencies...")
    import telebot
    logger.info("✅ telebot imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import telebot: {e}")
    exit(1)

# التوكن من متغير البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found in environment variables!")
    exit(1)

# إنشاء كائن البوت
bot = telebot.TeleBot(BOT_TOKEN)
logger.info("🤖 Bot instance created successfully")

def format_offer_message(offer, index):
    """تنسيق رسالة العرض"""
    title = offer.get('title', 'بدون عنوان')
    if len(title) > 60:
        title = title[:60] + "..."
    
    return f"""
{offer.get('emoji', '🔥')} **العرض #{index} - {offer.get('offer_type', 'عرض خاص')}**

🏷 **{title}**

💰 **السعر:** ${offer.get('current_price', 'N/A')} 
📉 **الخصم الحقيقي:** {offer.get('real_discount', 0)}%
⏰ **{offer.get('time_text', 'صالح اليوم')}**

⭐ **التقييم:** {offer.get('rating', 'N/A')}/5
🛒 **تم بيع:** {offer.get('sales', 0)} قطعة

📊 **قوة العرض:** {offer.get('hot_score', 0)} نقطة

🔗 [رابط الشراء]({offer.get('product_url', '#')})
"""

@bot.message_handler(commands=['start'])
def start_command(message):
    """أمر البدء"""
    try:
        welcome_text = """
🎯 **مرحباً بك في بوت العروض الحصرية!**

✅ **الأوامر المتاحة:**
/start - عرض هذه الرسالة  
/hot - أفضل العروض الساخنة 🏆
/عروض - العروض المميزة اليومية
/help - المساعدة
/test - اختبار البوت

🔥 **احصل على أفضل العروض من AliExpress بخصومات حقيقية!**
        """
        bot.reply_to(message, welcome_text, parse_mode='Markdown')
        logger.info(f"✅ Start command handled for user {message.chat.id}")
    except Exception as e:
        logger.error(f"❌ Error in start command: {e}")

@bot.message_handler(commands=['test'])
def test_command(message):
    """أمر اختباري"""
    try:
        response = "✅ **البوت يعمل بشكل ممتاز!**\n\n"
        response += f"🆔 **رقم الدردشة:** {message.chat.id}\n"
        response += f"👤 **المستخدم:** {message.from_user.first_name}\n"
        response += f"⏰ **الوقت:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        response += "🚀 **جرب /hot لرؤية العروض!**"
        
        bot.reply_to(message, response, parse_mode='Markdown')
        logger.info(f"✅ Test command handled for user {message.chat.id}")
    except Exception as e:
        logger.error(f"❌ Error in test command: {e}")

@bot.message_handler(commands=['hot', 'عروض'])
def hot_offers_command(message):
    """أمر العروض الساخنة"""
    try:
        logger.info(f"🚀 Hot offers command received from {message.chat.id}")
        
        # إرسال رسالة انتظار
        wait_msg = bot.reply_to(message, "🔍 **جاري البحث عن أفضل العروض الساخنة...**", parse_mode='Markdown')
        
        # جلب العروض
        import asyncio
        hot_offers = asyncio.run(advanced_api.get_real_discounts())
        
        # تصفية العروض
        filtered_offers = product_filter.filter_hot_products(hot_offers)
        
        if not filtered_offers:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
                text="⚠️ **لا توجد عروض ساخنة حالياً**\n\nجرب مرة أخرى بعد ساعة 🕒", 
                parse_mode='Markdown'
            )
            return
        
        # تحديث رسالة الانتظار
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text=f"🎯 **تم العثور على {len(filtered_offers)} عرض ساخن**\n\n**أفضل العروض اليوم:** 👇", 
            parse_mode='Markdown'
        )
        
        # إرسال أفضل 5 عروض
        for i, offer in enumerate(filtered_offers[:5], 1):
            offer_message = format_offer_message(offer, i)
            bot.send_message(
                message.chat.id, 
                offer_message, 
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            time.sleep(0.5)  # تجنب rate limits
            
        logger.info(f"✅ Sent {len(filtered_offers[:5])} offers to user {message.chat.id}")
            
    except Exception as e:
        logger.error(f"❌ Error in hot offers command: {e}")
        try:
            bot.reply_to(message, "❌ **حدث خطأ أثناء جلب العروض**\n\nجرب مرة أخرى بعد قليل ⏳", parse_mode='Markdown')
        except:
            pass

@bot.message_handler(commands=['help'])
def help_command(message):
    """أمر المساعدة"""
    try:
        help_text = """
🆘 **مساعدة البوت**

🎯 **كيف تحصل على أفضل العروض؟**
1. استخدم /hot للعروض الساخنة
2. استخدم /عروض للعروض اليومية  
3. تابع البوت يومياً للعروض المحدودة

🔥 **مميزات البوت:**
- ✅ عروض بخصومات حقيقية (30%+)
- ✅ منتجات عالية التقييم (4.0+)
- ✅ عروض محدودة الوقت
- ✅ روابط شراء مباشرة

⚡ **الأوامر المتاحة:**
/start - بدء الاستخدام
/hot - أفضل العروض
/عروض - عروض اليوم
/test - اختبار البوت
/help - هذه الرسالة

📞 **لل دعم:** تواصل مع المطور
        """
        bot.reply_to(message, help_text, parse_mode='Markdown')
        logger.info(f"✅ Help command handled for user {message.chat.id}")
    except Exception as e:
        logger.error(f"❌ Error in help command: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """معالجة جميع الرسائل الأخرى"""
    try:
        if message.text:
            response = f"🤖 **مرحباً {message.from_user.first_name}!**\n\n"
            response += "استخدم أحد الأوامر التالية:\n"
            response += "📍 /start - للبدء\n"
            response += "🔥 /hot - لأفضل العروض\n" 
            response += "🆘 /help - للمساعدة\n"
            response += "⚡ /test - لاختبار البوت"
            
            bot.reply_to(message, response, parse_mode='Markdown')
            logger.info(f"📩 Handled text message from {message.chat.id}")
    except Exception as e:
        logger.error(f"❌ Error handling message: {e}")

def start_polling():
    """بدء نظام Polling"""
    logger.info("🔄 Starting polling system...")
    
    try:
        # اختبار الاتصال أولاً
        bot_info = bot.get_me()
        logger.info(f"✅ Bot connected successfully: @{bot_info.username}")
        
        # بدء البوت
        logger.info("🚀 Bot is now running with polling...")
        logger.info("📱 Send /test to check if bot is working")
        
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            logger_level=logging.INFO
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        logger.info("🔄 Restarting in 10 seconds...")
        time.sleep(10)
        start_polling()

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🤖 ALIEXPRESS BOT STARTING...")
    logger.info("=" * 50)
    
    start_polling()
