import json
import telebot
from telebot import types
import re
import os
from urllib.parse import urlparse, parse_qs
import urllib.parse
import requests
from dotenv import load_dotenv
import time
import logging

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize the bot with the token
TELEGRAM_TOKEN_BOT = os.getenv('TELEGRAM_BOT_TOKEN')
ALIEXPRESS_API_PUBLIC = os.getenv('ALIEXPRESS_API_PUBLIC')
ALIEXPRESS_API_SECRET = os.getenv('ALIEXPRESS_API_SECRET')

# التحقق من المتغيرات البيئية لـ Railway
def check_environment():
    """التحقق من متغيرات البيئة"""
    if not TELEGRAM_TOKEN_BOT:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
        logger.info("💡 Please add TELEGRAM_BOT_TOKEN to Railway Environment Variables")
        return False
    
    if not ALIEXPRESS_API_PUBLIC or not ALIEXPRESS_API_SECRET:
        logger.warning("⚠️ AliExpress API keys not found - some features may not work")
    
    logger.info("✅ Environment check passed")
    return True

if not check_environment():
    exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN_BOT)

# محاولة تهيئة AliExpress API
aliexpress = None
try:
    from aliexpress_api import AliexpressApi, models
    if ALIEXPRESS_API_PUBLIC and ALIEXPRESS_API_SECRET:
        aliexpress = AliexpressApi(ALIEXPRESS_API_PUBLIC, ALIEXPRESS_API_SECRET,
                                   models.Language.AR, models.Currency.EUR, 'telegram_bot')
        logger.info("✅ AliExpress API initialized successfully")
    else:
        logger.warning("⚠️ AliExpress API not initialized - missing keys")
except ImportError:
    logger.error("❌ aliexpress-api library not installed!")
except Exception as e:
    logger.error(f"❌ Error initializing AliExpress API: {e}")

# Define keyboards
def create_keyboards():
    """إنشاء لوحات المفاتيح"""
    keyboardStart = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_DdwUZVd")
    btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
    btn3 = types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="https://t.me/ShopAliExpressMaroc")
    btn4 = types.InlineKeyboardButton("🎬 شاهد كيفية عمل البوت 🎬", url="https://t.me/ShopAliExpressMaroc/9")
    keyboardStart.add(btn1, btn2, btn3, btn4)

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_DdwUZVd")
    btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
    btn3 = types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="https://t.me/ShopAliExpressMaroc")
    keyboard.add(btn1, btn2, btn3)

    keyboard_games = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_DdwUZVd")
    btn2 = types.InlineKeyboardButton("⭐️ لعبة Merge boss ⭐️", url="https://s.click.aliexpress.com/e/_DlCyg5Z")
    btn3 = types.InlineKeyboardButton("⭐️ لعبة Fantastic Farm ⭐️", url="https://s.click.aliexpress.com/e/_DBBkt9V")
    btn4 = types.InlineKeyboardButton("⭐️ لعبة قلب الاوراق Flip ⭐️", url="https://s.click.aliexpress.com/e/_DdcXZ2r")
    keyboard_games.add(btn1, btn2, btn3, btn4)

    return keyboardStart, keyboard, keyboard_games

keyboardStart, keyboard, keyboard_games = create_keyboards()

# Define function to get exchange rate from USD to MAD
def get_usd_to_mad_rate():
    """الحصول على سعر صرف USD إلى MAD"""
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
        data = response.json()
        return data['rates']['MAD']
    except Exception as e:
        logger.error(f"❌ Error fetching exchange rate: {e}")
        return 10.0  # قيمة افتراضية

# نسخة مبسطة من استخراج معرف المنتج
def extract_product_id_simple(link):
    """استخراج معرف المنتج بشكل مبسط"""
    try:
        # الأنماط الأساسية
        patterns = [
            r'/item/(\d+)\.html',
            r'productIds=(\d+)',
            r'/(\d{9,})\.html',
            r'[?&]id=(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                product_id = match.group(1)
                logger.info(f"✅ Extracted product ID: {product_id}")
                return product_id
        
        # البحث عن أي رقم طويل
        numbers = re.findall(r'\d{9,}', link)
        if numbers:
            return max(numbers, key=len)
            
        return None
    except Exception as e:
        logger.error(f"❌ Error extracting product ID: {e}")
        return None

# وظيفة آمنة للحصول على الروابط التابعة
def safe_get_affiliate_link(url):
    """الحصول على رابط تابع بشكل آمن"""
    if not aliexpress:
        return None
        
    try:
        links = aliexpress.get_affiliate_links(url)
        if links and len(links) > 0:
            return links[0].promotion_link
        return None
    except Exception as e:
        logger.error(f"❌ Error getting affiliate link: {e}")
        return None

# Generate coin-index affiliate link
def generate_coin_affiliate_link(product_id):
    """إنشاء رابط عملات"""
    try:
        coin_url = f"https://m.aliexpress.com/p/coin-index/index.html?productIds={product_id}"
        return safe_get_affiliate_link(coin_url)
    except Exception as e:
        logger.error(f"❌ Error generating coin link: {e}")
        return None

# Generate bundle affiliate link
def generate_bundle_affiliate_link(product_id):
    """إنشاء رابط باندل"""
    try:
        original_link = f"https://www.aliexpress.com/item/{product_id}.html"
        encoded_url = urllib.parse.quote_plus(original_link)
        bundle_url = f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType=560'
        return safe_get_affiliate_link(bundle_url)
    except Exception as e:
        logger.error(f"❌ Error generating bundle link: {e}")
        return None

# Define bot handlers
@bot.message_handler(commands=['start'])
def welcome_user(message):
    """ترحيب بالمستخدم"""
    try:
        logger.info(f"👋 User {message.chat.id} started the bot")
        welcome_text = """مرحبا بكم👋 

أنا علي إكسبريس بوت أقوم بتخفيض المنتجات والبحث عن أفضل العروض 

🎯 **كيفية الاستخدام:**
1. انسخ رابط المنتج من AliExpress
2. أرسل الرابط هنا
3. سأرسل لك أفضل العروض والخصومات

🔥 **خصومات تصل إلى 80%**"""
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=keyboardStart)
    except Exception as e:
        logger.error(f"❌ Start command error: {e}")

@bot.message_handler(commands=['help'])
def help_command(message):
    """مساعدة"""
    help_text = """🆘 **مساعدة**

📋 **الأوامر:**
/start - بدء البوت
/help - هذه الرسالة

🔗 **كيفية الاستخدام:**
أرسل رابط منتج من AliExpress وسأبحث عن أفضل العروض

💰 **المميزات:**
• عروض عملات مخفضة
• عروض حزمة متنوعة
• عروض سوبر محدودة"""
    
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """معالجة جميع الرسائل"""
    try:
        logger.info(f"📨 Message from {message.chat.id}: {message.text[:50]}...")
        
        # استخراج الرابط
        link_match = re.search(r'https?://[^\s]+', message.text)
        if not link_match or "aliexpress.com" not in message.text:
            bot.send_message(message.chat.id, "❌ يرجى إرسال رابط منتج صحيح من AliExpress")
            return

        link = link_match.group()
        sent_msg = bot.send_message(message.chat.id, '⏳ جاري البحث عن أفضل العروض...')

        # معالجة الرابط
        process_product_link(message, link, sent_msg.message_id)
        
    except Exception as e:
        logger.error(f"❌ Error handling message: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء المعالجة")

def process_product_link(message, link, message_id):
    """معالجة رابط المنتج"""
    try:
        # استخراج معرف المنتج
        product_id = extract_product_id_simple(link)
        if not product_id:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, "❌ لم أتمكن من التعرف على المنتج. تأكد من الرابط")
            return

        logger.info(f"🎯 Processing product: {product_id}")

        # إنشاء الروابط التابعة
        coin_link = generate_coin_affiliate_link(product_id)
        bundle_link = generate_bundle_affiliate_link(product_id)
        super_link = safe_get_affiliate_link(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=562'
        )
        limit_link = safe_get_affiliate_link(
            f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={link}?sourceType=561'
        )

        # بناء الرسالة
        message_text = "🛍 **أفضل العروض للمنتج:**\n\n"

        if coin_link:
            message_text += f"💰 **عرض العملات:**\n{coin_link}\n\n"

        if bundle_link:
            message_text += f"📦 **عرض الحزمة:**\n{bundle_link}\n\n"

        if super_link:
            message_text += f"💎 **عرض السوبر:**\n{super_link}\n\n"

        if limit_link:
            message_text += f"🔥 **عرض محدود:**\n{limit_link}\n\n"

        message_text += "🎯 **قارن الأسعار واختر الأفضل!**"

        # إرسال النتيجة
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id, message_text, reply_markup=keyboard)
        
        logger.info(f"✅ Sent offers for product {product_id}")

    except Exception as e:
        logger.error(f"❌ Error processing product: {e}")
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء معالجة المنتج")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    """معالجة الضغطات"""
    try:
        if call.data == 'click':
            bot.send_message(call.message.chat.id, 
                           "🛒 لتخفيض سلة التسوق، أرسل رابط سلة التسوق من AliExpress")
        else:
            bot.answer_callback_query(call.id, "⚙️ جاري التحميل...")
    except Exception as e:
        logger.error(f"❌ Callback error: {e}")

def main():
    """الدالة الرئيسية"""
    try:
        logger.info("=" * 50)
        logger.info("🤖 ALIEXPRESS BOT - STARTING...")
        logger.info("=" * 50)
        
        # معلومات الخادم
        try:
            ip = requests.get('https://api.ipify.org', timeout=10).text
            logger.info(f"🌐 Server IP: {ip}")
        except:
            logger.info("🌐 Could not get server IP")
        
        # تنظيف الـ webhooks السابقة
        try:
            bot.remove_webhook()
            logger.info("✅ Webhooks cleaned")
        except:
            pass
        
        # بدء البوت
        logger.info("🔄 Bot is running in POLLING mode...")
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=45,
            logger_level=logging.INFO
        )
        
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")

if __name__ == "__main__":
    main()
