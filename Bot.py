import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from api import advanced_api
from product_filter import product_filter
import asyncio

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# التوكن من متغير البيئة
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

def format_offer_message(offer, index):
    """تنسيق رسالة العرض"""
    title = offer.get('title', 'بدون عنوان')
    if len(title) > 60:
        title = title[:60] + "..."
    
    return f"""
{offer.get('emoji', '🔥')} **العرض #{index} - {offer.get('offer_type', 'عرض خاص')}**

🏷 **{title}**

💰 **السعر:** ${offer.get('current_price', 'N/A')} 
   ~~${offer.get('original_price', 'N/A')}~~
📉 **الخصم الحقيقي:** {offer.get('real_discount', 0)}%
⏰ **{offer.get('time_text', 'صالح اليوم')}**

⭐ **التقييم:** {offer.get('rating', 'N/A')}/5
🛒 **تم بيع:** {offer.get('sales', 0)} قطعة

🔗 **رابط الشراء:** [اضغط هنا]({offer.get('product_url', '#')})

📊 **قوة العرض:** {offer.get('hot_score', 0)} نقطة
"""

async def start_command(update: Update, context: CallbackContext):
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
    await update.message.reply_text(welcome_text)

async def hot_offers_command(update: Update, context: CallbackContext):
    """أمر العروض الساخنة"""
    try:
        # إرسال رسالة انتظار
        wait_msg = await update.message.reply_text("🔍 **جاري البحث عن أفضل العروض الساخنة...**")
        
        # جلب العروض من المصادر المتقدمة
        hot_offers = await advanced_api.get_real_discounts()
        
        # تصفية العروض
        filtered_offers = product_filter.filter_hot_products(hot_offers)
        
        if not filtered_offers:
            await wait_msg.edit_text("⚠️ **لا توجد عروض ساخنة حالياً**\nجرب مرة أخرى بعد ساعة 🕒")
            return
        
        # إرسال رسالة النتائج
        await wait_msg.edit_text(f"🎯 **تم العثور على {len(filtered_offers)} عرض ساخن**\n\n**أفضل العروض اليوم:**")
        
        # إرسال أفضل 5 عروض
        for i, offer in enumerate(filtered_offers[:5], 1):
            offer_message = format_offer_message(offer, i)
            await update.message.reply_text(offer_message, disable_web_page_preview=True)
            
    except Exception as e:
        logger.error(f"Error in hot offers command: {str(e)}")
        await update.message.reply_text("❌ حدث خطأ أثناء جلب العروض. جرب مرة أخرى لاحقاً.")

async def help_command(update: Update, context: CallbackContext):
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
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: CallbackContext):
    """معالجة الرسائل النصية"""
    text = update.message.text
    await update.message.reply_text("🤖 استخدم /hot للحصول على أفضل العروض!")

async def error_handler(update: Update, context: CallbackContext):
    """معالج الأخطاء"""
    logger.error(f"Error: {context.error}")

def main():
    """الدالة الرئيسية"""
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("hot", hot_offers_command))
    application.add_handler(CommandHandler("عروض", hot_offers_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    print("🤖 البوت يعمل الآن...")
    application.run_polling()

if __name__ == '__main__':
    main()
