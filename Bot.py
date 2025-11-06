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
import hashlib
import random

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
AFFILIATE_PID = os.getenv('AFFILIATE_PID', 'mm_123456789_1234567_12345678')

# التحقق من المتغيرات البيئية لـ Railway
def check_environment():
    """التحقق من متغيرات البيئة"""
    if not TELEGRAM_TOKEN_BOT:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found!")
        logger.info("💡 Please add TELEGRAM_BOT_TOKEN to Railway Environment Variables")
        return False
    
    logger.info("✅ Environment check passed")
    return True

if not check_environment():
    exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN_BOT)

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

def validate_aliexpress_link(link):
    """التحقق من أن الرابط من AliExpress"""
    ali_domains = [
        'aliexpress.com',
        'alibaba.com',
        's.click.aliexpress.com',
        'm.aliexpress.com',
        'star.aliexpress.com'
    ]
    
    return any(domain in link for domain in ali_domains)

def resolve_redirects(link):
    """حل التوجيهات للحصول على الرابط النهائي"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(link, headers=headers, timeout=10, allow_redirects=True)
        final_url = response.url
        logger.info(f"🔗 Redirect resolved: {link} -> {final_url}")
        return final_url
    except Exception as e:
        logger.error(f"❌ Error resolving redirects: {e}")
        return link

def extract_product_id_simple(link):
    """استخراج معرف المنتج بشكل محسن"""
    try:
        logger.info(f"🔍 Extracting product ID from: {link}")
        
        # تنظيف الرابط أولاً
        clean_link = link.split('?')[0]  # إزالة parameters
        
        # الأنماط المحسنة
        patterns = [
            r'/item/(\d{8,})\.html',
            r'/_m/(\d{8,})',
            r'productIds=(\d{8,})',
            r'[?&]id=(\d{8,})',
            r'/(\d{8,})(?:\.html|$)',
            r's\.click\.aliexpress\.com/e/.*?/(\d{8,})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, clean_link)
            if match:
                product_id = match.group(1)
                if 8 <= len(product_id) <= 15:
                    logger.info(f"✅ Extracted product ID: {product_id} using pattern: {pattern}")
                    return product_id
        
        numbers = re.findall(r'\d{8,}', link)
        if numbers:
            for num in numbers:
                if 8 <= len(num) <= 15:
                    logger.info(f"✅ Extracted product ID (fallback): {num}")
                    return num
        
        logger.warning(f"❌ No valid product ID found in: {link}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error extracting product ID: {e}")
        return None

def generate_unique_affiliate_links(product_id, original_link):
    """إنشاء روابط تابعة فريدة لكل نوع"""
    try:
        affiliate_pid = AFFILIATE_PID
        
        base_url = "https://s.click.aliexpress.com/e/"
        
        # أكواد فريدة لكل نوع من العروض
        links = {
            'direct': {
                'url': f"{base_url}_DlK9gV7_{affiliate_pid}_{product_id}",
                'name': '🛒 الشراء المباشر',
                'desc': 'شراء مباشر - أفضل عرض متاح'
            },
            'coins': {
                'url': f"{base_url}_DdF9HAf_{affiliate_pid}_{product_id}",
                'name': '💰 عرض العملات',
                'desc': 'خصم إضافي باستخدام عملات AliExpress'
            },
            'super': {
                'url': f"{base_url}_DmPtwSD_{affiliate_pid}_{product_id}",
                'name': '💎 عرض السوبر',
                'desc': 'عروض خاصة حصرية لفترة محدودة'
            },
            'bundle': {
                'url': f"{base_url}_DehY1K9_{affiliate_pid}_{product_id}",
                'name': '📦 عرض الحزمة', 
                'desc': 'عروض مجمعة بخصومات كبيرة'
            },
            'flash': {
                'url': f"{base_url}_DkXq8YJ_{affiliate_pid}_{product_id}",
                'name': '⚡ عرض فلاش',
                'desc': 'عروض سريعة تنتهي قريباً'
            }
        }
        
        logger.info(f"💰 Generated {len(links)} unique affiliate links")
        return links
        
    except Exception as e:
        logger.error(f"❌ Error generating unique links: {e}")
        return {}

def get_product_image(product_id):
    """الحصول على صورة المنتج"""
    try:
        # محاولة جلب صورة المنتج من AliExpress
        image_url = f"https://ae01.alicdn.com/kf/{product_id[:2]}/{product_id}.jpg"
        
        # التحقق من وجود الصورة
        response = requests.head(image_url, timeout=5)
        if response.status_code == 200:
            logger.info(f"🖼️ Found product image: {image_url}")
            return image_url
        
        # محاولة ثانية بصيغة مختلفة
        image_url2 = f"https://ae01.alicdn.com/kf/{product_id}.jpg"
        response2 = requests.head(image_url2, timeout=5)
        if response2.status_code == 200:
            logger.info(f"🖼️ Found product image: {image_url2}")
            return image_url2
        
        # صور بديلة حسب نوع المنتج
        fallback_images = {
            'electronics': 'https://ae01.alicdn.com/kf/S1df934c441e14d3e9a4e86f3097153b3E.png',
            'fashion': 'https://ae01.alicdn.com/kf/S1df934c441e14d3e9a4e86f3097153b3E.png',
            'home': 'https://ae01.alicdn.com/kf/S1df934c441e14d3e9a4e86f3097153b3E.png',
            'default': 'https://ae01.alicdn.com/kf/S1df934c441e14d3e9a4e86f3097153b3E.png'
        }
        
        logger.info("🖼️ Using fallback product image")
        return fallback_images['default']
        
    except Exception as e:
        logger.error(f"❌ Error getting product image: {e}")
        return "https://ae01.alicdn.com/kf/S1df934c441e14d3e9a4e86f3097153b3E.png"

def get_product_title_fallback(product_id):
    """إنشاء عنوان افتراضي للمنتج"""
    categories = [
        "منتج إلكتروني متميز",
        "أحدث صيحات الموضة",
        "أدوات منزلية ذكية",
        "جهاز تقني متطور",
        "إكسسوارات عصرية"
    ]
    
    return f"{random.choice(categories)} #{product_id}"

# Define bot handlers
@bot.message_handler(commands=['start'])
def welcome_user(message):
    """ترحيب بالمستخدم"""
    try:
        logger.info(f"👋 User {message.chat.id} started the bot")
        welcome_text = """🌐 **BotFinder - بوت العروض الحصرية**  

🎯 **مرحباً بك! أنا متخصص في:**  
• إنشاء عروض حصرية لمنتجات AliExpress  
• توفير روابط تابعة بخصومات  
• البحث عن أفضل العروض المتاحة  

🚀 **كيفية الاستخدام:**
1. انسخ رابط أي منتج من AliExpress
2. أرسل الرابط هنا
3. سأرسل لك روابط حصرية بخصومات

💰 **جميع الروابط تدعم البوت وتحقق عمولة**
⭐️ **ابدأ الآن وأرسل رابط منتج!**"""
        
        bot.send_message(message.chat.id, welcome_text, reply_markup=keyboardStart)
    except Exception as e:
        logger.error(f"❌ Start command error: {e}")

@bot.message_handler(commands=['help'])
def help_command(message):
    """مساعدة"""
    help_text = """🆘 **مساعدة BotFinder**

📋 **الأوامر المتاحة:**
/start - بدء البوت
/help - هذه الرسالة
/affiliate - معلومات الشراكة

🔗 **كيفية الاستخدام:**
أرسل رابط منتج من AliExpress وسأبحث عن أفضل العروض

💰 **مميزات البوت:**
• روابط تابعة تحقق عمولة للبوت
• عروض حصرية بخصومات
• دعم متواصل 24/7

📝 **أمثلة للروابط الصحيحة:**
• https://www.aliexpress.com/item/1005005123456789.html
• https://s.click.aliexpress.com/e/_DmqR7ZV"""
    
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['affiliate'])
def affiliate_info(message):
    """معلومات الشراكة"""
    affiliate_text = f"""💼 **معلومات نظام الشراكة**

🔗 **معرف الشراكة الحالي:** `{AFFILIATE_PID}`

💰 **كيف تعمل العمولة:**
• كل عملية شراء عبر الروابط تحقق عمولة
• العمولة تتراوح بين 4-12% حسب المنتج
• يتم تحديث الأرباح بشكل دوري

🎯 **لتحقيق أعلى أرباح:**
• شارك البوت مع الأصدقاء
• استخدم الروابط في مجموعاتك
• شجع الآخرين على استخدام البوت

📊 **لإعداد PID خاص بك:**
1. سجل في AliExpress Affiliate
2. احصل على PID الخاص بك
3. أضفه في متغيرات البيئة"""
    
    bot.send_message(message.chat.id, affiliate_text)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """معالجة جميع الرسائل"""
    try:
        logger.info(f"📨 Message from {message.chat.id}: {message.text[:50]}...")
        
        # استخراج الرابط
        link_match = re.search(r'https?://[^\s]+', message.text)
        if not link_match:
            bot.send_message(message.chat.id, "❌ يرجى إرسال رابط منتج صحيح من AliExpress")
            return

        link = link_match.group()
        
        # التحقق من أن الرابط من AliExpress
        if not validate_aliexpress_link(link):
            bot.send_message(message.chat.id, "❌ هذا الرابط ليس من AliExpress. يرجى إرسال رابط منتج من AliExpress فقط")
            return

        sent_msg = bot.send_message(message.chat.id, '⏳ جاري البحث عن أفضل العروض...')

        # معالجة الرابط
        process_product_link(message, link, sent_msg.message_id)
        
    except Exception as e:
        logger.error(f"❌ Error handling message: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء المعالجة")

def process_product_link(message, link, message_id):
    """معالجة رابط المنتج مع صور وروابط فريدة"""
    try:
        # حل التوجيهات أولاً
        resolved_link = resolve_redirects(link)
        logger.info(f"🔗 Using resolved link: {resolved_link}")
        
        # استخراج معرف المنتج
        product_id = extract_product_id_simple(resolved_link)
        if not product_id:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, "❌ لم أتمكن من التعرف على المنتج")
            return

        logger.info(f"🎯 Processing product: {product_id}")

        # إنشاء روابط عمولة فريدة
        affiliate_links = generate_unique_affiliate_links(product_id, resolved_link)
        
        # الحصول على صورة المنتج
        product_image = get_product_image(product_id)
        
        # الحصول على عنوان المنتج
        product_title = get_product_title_fallback(product_id)

        # بناء الرسالة مع تنسيق محسن
        message_text = f"🎁 **{product_title}**\n\n"
        message_text += f"📦 **معرف المنتج:** `{product_id}`\n\n"
        message_text += "🎯 **اختر أحد العروض الحصرية:**\n\n"

        links_count = 0
        
        for link_type, link_info in affiliate_links.items():
            message_text += f"**{link_info['name']}**\n"
            message_text += f"📝 {link_info['desc']}\n"
            message_text += f"🔗 {link_info['url']}\n\n"
            links_count += 1

        message_text += "---\n"
        message_text += "💸 **جميع الروابط أعلاه تدعم البوت وتحقق عمولة**\n"
        message_text += "⭐️ *شكراً لدعمك واستخدامك البوت!*"

        # إرسال النتيجة مع الصورة
        bot.delete_message(message.chat.id, message_id)
        
        try:
            # محاولة إرسال الصورة مع النص
            bot.send_photo(
                message.chat.id,
                product_image,
                caption=message_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            logger.info(f"🖼️ Sent message with product image")
        except Exception as photo_error:
            logger.error(f"❌ Error sending photo: {photo_error}")
            # إذا فشل إرسال الصورة، أرسل النص فقط
            bot.send_message(
                message.chat.id, 
                message_text, 
                reply_markup=keyboard, 
                parse_mode='Markdown',
                disable_web_page_preview=False
            )
            logger.info(f"📝 Sent message without image")
        
        logger.info(f"💰 Sent {links_count} unique affiliate links for product {product_id}")

    except Exception as e:
        logger.error(f"❌ Error processing product: {e}")
        bot.delete_message(message.chat.id, message_id)
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء معالجة المنتج")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    """معالجة الضغطات"""
    try:
        if call.data == 'click':
            help_text = """🛒 **تخفيض سلة التسوق**

لحصول على تخفيض على سلة التسوق:
1. اذهب إلى سلة التسوق في AliExpress
2. انسخ رابط السلة
3. أرسل الرابط هنا

📝 **رابط سلة التسوق يبدو مثل:**
https://www.aliexpress.com/p/shoppingcart/index.html?..."""
            
            bot.send_message(call.message.chat.id, help_text)
        else:
            bot.answer_callback_query(call.id, "⚙️ جاري التحميل...")
    except Exception as e:
        logger.error(f"❌ Callback error: {e}")

def main():
    """الدالة الرئيسية"""
    try:
        logger.info("=" * 50)
        logger.info("🤖 BOTFINDER AFFILIATE BOT - STARTING...")
        logger.info("=" * 50)
        
        # معلومات الخادم
        try:
            ip = requests.get('https://api.ipify.org', timeout=10).text
            logger.info(f"🌐 Server IP: {ip}")
        except:
            logger.info("🌐 Could not get server IP")
        
        # معلومات الشراكة
        if AFFILIATE_PID and AFFILIATE_PID != "mm_123456789_1234567_12345678":
            logger.info(f"💰 Using affiliate PID: {AFFILIATE_PID}")
        else:
            logger.warning("⚠️ Using default affiliate PID - configure AFFILIATE_PID for real earnings")
        
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
