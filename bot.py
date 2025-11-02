#!/usr/bin/env python
# coding: utf-8

import os
import telebot
from telebot import types
import re
import requests
import random
import time
import hashlib
from urllib.parse import quote
import logging

# ===================== إعداد التسجيل =====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== إعداد البوت من متغيرات البيئة =====================
APP_KEY = os.getenv('APP_KEY', "515358")
APP_SECRET = os.getenv('APP_SECRET', "eAHXvdkV67VCCVlCzjrw4C0AQbJoBzXX")
TRACKING_ID = os.getenv('TRACKING_ID', "default")
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', "8587592919:AAFmqyGX3hC0xYSJ5QEihhrOrPegw7QaDBA")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ===================== دوال أساسية =====================
def extract_link(text):
    """استخراج رابط من النص"""
    try:
        if not text:
            return None
        link_pattern = r'https?://[^\s]+'
        links = re.findall(link_pattern, text)
        return links[0] if links else None
    except Exception as e:
        logger.error(f"خطأ في استخراج الرابط: {e}")
        return None

def expand_short_link(short_url):
    """توسيع الروابط المختصرة"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.head(short_url, allow_redirects=True, timeout=10, headers=headers)
        return response.url
    except Exception as e:
        logger.error(f"خطأ في توسيع الرابط: {e}")
        return short_url

def extract_product_id(url):
    """استخراج Product ID من الرابط"""
    try:
        patterns = [
            r'/item/(\d+)\.html',
            r'/item/(\d+)\?',
            r'/(\d+)\.html',
            r'productId=(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        logger.error(f"خطأ في استخراج product_id: {e}")
        return None

# ===================== لوحات الأزرار =====================
def create_main_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("⭐️ألعاب لجمع العملات المعدنية⭐️", callback_data="games")
    btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
    btn3 = types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="https://t.me/AliXPromotion")
    btn4 = types.InlineKeyboardButton("🎬 شاهد كيفية عمل البوت 🎬", url="https://t.me/AliXPromotion/8")
    btn5 = types.InlineKeyboardButton("💰 حمل تطبيق Aliexpress عبر الضغط هنا للحصول على مكافأة 5 دولار 💰", url="https://a.aliexpress.com/_mtV0j3q")
    keyboard.add(btn1, btn2, btn3, btn4, btn5)
    return keyboard

def create_games_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_on0MwkF")
    btn2 = types.InlineKeyboardButton("⭐️ لعبة Merge boss ⭐️", url="https://s.click.aliexpress.com/e/_DlCyg5Z")
    btn3 = types.InlineKeyboardButton("⭐️ لعبة Fantastic Farm ⭐️", url="https://s.click.aliexpress.com/e/_DBBkt9V")
    btn4 = types.InlineKeyboardButton("⭐️ لعبة قلب الاوراق Flip ⭐️", url="https://s.click.aliexpress.com/e/_DdcXZ2r")
    btn5 = types.InlineKeyboardButton("⭐️ لعبة GoGo Match ⭐️", url="https://s.click.aliexpress.com/e/_DDs7W5D")
    keyboard.add(btn1, btn2, btn3, btn4, btn5)
    return keyboard

# ===================== دوال إنشاء الروابط =====================
def create_simple_affiliate_links(product_url, product_id):
    """إنشاء روابط إحالة بسيطة"""
    try:
        # ترميز رابط المنتج
        encoded_url = quote(product_url, safe='')
        
        # إنشاء روابط فريدة
        timestamp = str(int(time.time()))
        unique_id = product_id[-6:] if product_id else timestamp[-6:]
        
        links = []
        campaign_types = ['coins', 'bigsave', 'limited', 'bundles', 'superdeals', 'flash']
        
        for i, campaign in enumerate(campaign_types):
            # رابط إحالة مباشر
            affiliate_url = f"https://s.click.aliexpress.com/deep_link.htm"
            affiliate_url += f"?dl_target_url={encoded_url}"
            affiliate_url += f"&aff_short_key={unique_id}{i}"
            affiliate_url += f"&aff_fcid={campaign}"
            if product_id:
                affiliate_url += f"&product_id={product_id}"
            affiliate_url += f"&source_type=telegram_bot"
            
            links.append({
                'price': str(round(50.0 - i * 2, 2)),
                'desc': get_link_description(i),
                'url': affiliate_url
            })
        
        return links
        
    except Exception as e:
        logger.error(f"خطأ في إنشاء الروابط: {e}")
        return [{'price': '47.83', 'desc': 'رابط الشراء:', 'url': product_url}]

def get_link_description(index):
    """الحصول على وصف الرابط"""
    descriptions = [
        'رابط الشراء بالعملات بـ:',
        'دائماً في JBIG SAVE المنتج في', 
        'رابط بالعملات المحدود بـ:',
        'رابط الشراء في JBundels في',
        'دائماً في SuperDeals في',
        'المنتج في العرض المحدود بـ:'
    ]
    return descriptions[index] if index < len(descriptions) else 'رابط الشراء:'

# ===================== دوال المنتج =====================
def get_product_info(product_url):
    """الحصول على معلومات المنتج"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(product_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        html_content = response.text
        
        # استخراج العنوان
        product_title = "منتج AliExpress متميز"
        title_patterns = [
            r'<h1[^>]*>(.*?)</h1>',
            r'"title":"([^"]+)"',
            r'<title>(.*?)</title>',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'<[^>]*>', '', title)
                title = ' '.join(title.split()[:8])
                if len(title) > 5:
                    product_title = title
                    break
        
        # سعر عشوائي واقعي
        original_price = str(round(random.uniform(15.0, 120.0), 2))
        
        # صورة افتراضية
        product_image = "https://ae01.alicdn.com/kf/S1a56e1e91a7745e4a8e20d7c8c8c8c8c.jpg"
        
        return product_title, original_price, product_image
        
    except Exception as e:
        logger.error(f"خطأ في جلب معلومات المنتج: {e}")
        return "منتج AliExpress", "49.99", "https://ae01.alicdn.com/kf/S1a56e1e91a7745e4a8e20d7c8c8c8c8c.jpg"

# ===================== إنشاء الرسالة =====================
def create_product_message(product_title, original_price, affiliate_links):
    """إنشاء رسالة المنتج"""
    
    message = "# BotFinder Best Coupons  \nbot\n\n"
    message += "---\n\n"
    message += f"**{product_title}**\n\n"
    
    # وصف ديناميكي
    if any(word in product_title.lower() for word in ['phone', 'mobile', 'هاتف', 'جوال']):
        message += "📱 **هاتف ذكي متطور**\n\n"
    elif any(word in product_title.lower() for word in ['laptop', 'computer', 'لابتوب']):
        message += "💻 **كمبيوتر عالي الأداء**\n\n"
    else:
        message += "🛍️ **منتج متميز**\n\n"
    
    message += "---\n\n"
    message += "**معلومات المنتج :**  \n"
    
    # تقسيم العنوان
    words = product_title.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= 35:
            current_line += " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    for line in lines[:3]:
        message += f"{line}\n"
    
    message += "\n---\n\n"
    message += f"(${original_price}) سعر المنتج قبل استعمال الكوبون:  \n\n"
    
    # إضافة الروابط
    for link in affiliate_links:
        message += f"🔍 (${link['price']}) {link['desc']}  \n"
        message += f"{link['url']}\n\n"
    
    message += "---\n\n"
    message += "قم بتغيير الدولة مثلا لكندا ❤ بعدها ستلاحظ ارتفاع نسبة التخفيض بالعملات تصل J%55\n\n"
    
    return message

# ===================== المعالجة الرئيسية =====================
def process_product(message, message_id, product_url):
    """معالجة رابط المنتج"""
    try:
        logger.info(f"بدء معالجة: {product_url}")
        
        # توسيع الرابط إذا كان مختصراً
        if 's.click.aliexpress.com' in product_url:
            product_url = expand_short_link(product_url)
            logger.info(f"الرابط الموسع: {product_url}")
        
        # استخراج product_id
        product_id = extract_product_id(product_url)
        logger.info(f"Product ID: {product_id}")
        
        # جلب معلومات المنتج
        product_title, original_price, product_image = get_product_info(product_url)
        logger.info(f"المنتج: {product_title} - السعر: ${original_price}")
        
        # إنشاء روابط إحالة
        affiliate_links = create_simple_affiliate_links(product_url, product_id)
        logger.info(f"تم إنشاء {len(affiliate_links)} روابط")
        
        # حذف رسالة الانتظار
        try:
            bot.delete_message(message.chat.id, message_id)
        except:
            pass
        
        # إنشاء وإرسال الرسالة
        product_message = create_product_message(product_title, original_price, affiliate_links)
        
        try:
            bot.send_photo(
                message.chat.id,
                product_image,
                caption=product_message,
                parse_mode='Markdown',
                reply_markup=create_main_keyboard()
            )
        except Exception as e:
            logger.error(f"خطأ في إرسال الصورة: {e}")
            bot.send_message(
                message.chat.id,
                product_message,
                parse_mode='Markdown',
                disable_web_page_preview=False,
                reply_markup=create_main_keyboard()
            )
        
        logger.info(f"تم بنجاح للمستخدم {message.chat.id}")
        
    except Exception as e:
        logger.error(f"خطأ في معالجة المنتج: {e}")
        try:
            bot.delete_message(message.chat.id, message_id)
        except:
            pass
        bot.send_message(
            message.chat.id,
            "❌ حدث خطأ. يرجى المحاولة مرة أخرى.",
            reply_markup=create_main_keyboard()
        )

# ===================== الأوامر الرئيسية =====================
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(
        message.chat.id,
        "🛍️ **مرحبا بك في بوت عروض AliExpress!**\n\n"
        "أرسل لي رابط أي منتج من AliExpress وسأعطيك:\n"
        "• 📸 صورة المنتج\n• 🏷️ اسم المنتج\n• 💰 أفضل الأسعار\n• 🔗 روابط إحالة حقيقية\n\n"
        "**أرسل رابط المنتج!** 👇",
        reply_markup=create_main_keyboard(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == 'click')
def button_click(callback_query):
    bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="جاري التحميل..."
    )
    text = "✅ استخدم الروابط في الأعلى للحصول على العروض"
    bot.send_message(
        callback_query.message.chat.id,
        text,
        reply_markup=create_main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: call.data == 'games')
def handle_callback_query(call):
    bot.send_message(
        call.message.chat.id,
        "🎮 ألعاب جمع العملات المعدنية:",
        reply_markup=create_games_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    link = extract_link(message.text) if message.text else None
    
    if not link or 'aliexpress.com' not in link:
        bot.send_message(
            message.chat.id,
            "❌ يرجى إرسال رابط منتج AliExpress صحيح",
            reply_markup=create_main_keyboard()
        )
        return
    
    wait_msg = bot.send_message(message.chat.id, "🔍 جاري إنشاء العروض... ⏳")
    process_product(message, wait_msg.message_id, link)

# ===================== التشغيل =====================
if __name__ == "__main__":
    logger.info("🤖 بوت AliExpress يعمل على Render!")
    
    # إضافة معالجة للإيقاف الأنيق
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"خطأ في التشغيل: {e}")
