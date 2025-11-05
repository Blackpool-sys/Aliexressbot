import os
import logging
import telebot
from api import advanced_api
from product_filter import product_filter
import asyncio

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# التوكن من متغير البيئة في Railway
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found in environment variables!")
    exit(1)

# إنشاء كائن البوت
bot = telebot.TeleBot(BOT_TOKEN)

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
    welcome_text = """
🎯 **مرحباً بك في بوت العروض الحصرية!**

✅ **الأوامر المتاحة:**
/start - عرض هذه الرسالة
/hot - أفضل العروض الساخنة 🏆
/عروض - العروض المميزة اليومية
/help - المساعدة

🔥 **احصل على أفضل العروض من AliExpress بخصومات حقيقية!**
    """
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['hot', 'عروض'])
def hot_offers_command(message):
    """أمر العروض الساخنة"""
    try:
        # إرسال رسالة انتظار
        wait_msg = bot.reply_to(message, "🔍 **جاري البحث عن أفضل العروض الساخنة...**", parse_mode='Markdown')
        
        # جلب العروض
        hot_offers = asyncio.run(advanced_api.get_real_discounts())
        
        # تصفية العروض
        filtered_offers = product_filter.filter_hot_products(hot_offers)
        
        if not filtered_offers:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
                text="⚠️ **لا توجد عروض ساخنة حالياً**\nجرب مرة أخرى بعد ساعة 🕒", 
                parse_mode='Markdown'
            )
            return
        
        # تحديث رسالة الانتظار
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text=f"🎯 **تم العثور على {len(filtered_offers)} عرض ساخن**\n\n**أفضل العروض اليوم:**", 
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
            
    except Exception as e:
        logger.error(f"Error in hot offers command: {str(e)}")
        bot.reply_to(message, "❌ حدث خطأ أثناء جلب العروض. جرب مرة أخرى لاحقاً.")

@bot.message_handler(commands=['help'])
def help_command(message):
    """أمر المساعدة"""
    help_text = """
🆘 **مساعدة البوت:**

🎯 **كيف تحصل على أفضل العروض؟**
1. استخدم /hot للعروض الساخنة
2. استخدم /عروض للعروض اليومية
3. تابع البوت يومياً للعروض المحدودة

🔥 **مميزات البوت:**
- عروض بخصومات حقيقية (30%+)
- منتجات عالية التقييم (4.0+)
- عروض محدودة الوقت
- روابط شراء مباشرة

📞 **لل دعم:** تواصل مع المطور
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """معالجة جميع الرسائل الأخرى"""
    bot.reply_to(message, "🤖 استخدم /hot للحصول على أفضل العروض!")

if __name__ == '__main__':
    logger.info("🤖 البوت يعمل الآن...")
    bot.infinity_polling()
