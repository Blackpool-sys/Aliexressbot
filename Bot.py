import json
import telebot
from flask import Flask, request
import threading
from telebot import types
from aliexpress_api import AliexpressApi, models
import re
import os
from urllib.parse import urlparse, parse_qs
import urllib.parse
import requests
from dotenv import load_dotenv
import time
import functools
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Initialize the bot with the token
TELEGRAM_TOKEN_BOT = os.getenv('TELEGRAM_BOT_TOKEN')
ALIEXPRESS_API_PUBLIC = os.getenv('ALIEXPRESS_API_PUBLIC')
ALIEXPRESS_API_SECRET = os.getenv('ALIEXPRESS_API_SECRET')

# Check if required environment variables are set
if not TELEGRAM_TOKEN_BOT:
    print("X Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
    print("Please set the environment variable or create a .env file with your bot token.")
    exit(1)

if not ALIEXPRESS_API_PUBLIC or not ALIEXPRESS_API_SECRET:
    print("X Error: ALIEXPRESS_API_PUBLIC and ALIEXPRESS_API_SECRET environment variables are not set!")
    print("Please set the environment variables or create a .env file with your API credentials.")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN_BOT)

# عرض IP الخادم فور التشغيل
try:
    ip = requests.get('https://api.ipify.org', timeout=5).text
    print(f"🎯🎯🎯 RAILWAY SERVER IP: {ip} 🎯🎯🎯")
    print(f"🎯 ADD THIS IP TO ALIEXPRESS WHITELIST: {ip}")
except Exception as e:
    print(f"❌ Could not get server IP: {e}")

# Initialize Aliexpress API
try:
    aliexpress = AliexpressApi(ALIEXPRESS_API_PUBLIC, ALIEXPRESS_API_SECRET,
                               models.Language.AR, models.Currency.EUR, 'telegrame_bot')
    print("AliExpress API initialized successfully.")
except Exception as e:
    print(f"Error initializing AliExpress API: {e}")

# Define keyboards
keyboardStart = types.InlineKeyboardMarkup(row_width=1)
btn1 = types.InlineKeyboardButton("⭐️ صفحة مراجعة وجمع النقاط يوميا ⭐️", url="https://s.click.aliexpress.com/e/_DdwUZVd")
btn2 = types.InlineKeyboardButton("⭐️تخفيض العملات على منتجات السلة 🛒⭐️", callback_data='click')
btn3 = types.InlineKeyboardButton("❤️ اشترك في القناة للمزيد من العروض ❤️", url="https://t.me/ShopAliExpressMaroc")
btn4 = types.InlineKeyboardButton("🎬 شاهد كيفية عمل البوت 🎬", url="https://t.me/ShopAliExpressMaroc/9")
btn5 = types.InlineKeyboardButton("💰 حمل تطبيق Aliexpress عبر الضغط هنا للحصول على مكافأة 5 دولار 💰", url="https://a.aliexpress.com/_mtV0j3q")
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
btn5 = types.InlineKeyboardButton("⭐️ لعبة GoGo Match ⭐️", url="https://s.click.aliexpress.com/e/_DDs7W5D")
keyboard_games.add(btn1, btn2, btn3, btn4, btn5)

# Simple Cache Implementation
class SimpleCache:
    def __init__(self, ttl=300):  # 5 دقائق
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return data
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, datetime.now())

# Initialize caches
product_cache = SimpleCache(ttl=600)  # 10 دقائق للمنتجات
exchange_cache = SimpleCache(ttl=3600)  # ساعة لسعر الصرف

# Define function to get exchange rate from USD to MAD
def get_usd_to_mad_rate():
    """الحصول على سعر صرف USD إلى MAD مع التخزين المؤقت"""
    cached_rate = exchange_cache.get('usd_mad_rate')
    if cached_rate:
        return cached_rate
    
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
        data = response.json()
        rate = data['rates']['MAD']
        exchange_cache.set('usd_mad_rate', rate)
        print(f"✅ تم تحديث سعر الصرف: 1 USD = {rate} MAD")
        return rate
    except Exception as e:
        print(f"❌ Error fetching exchange rate: {e}")
        return 10.0  # سعر افتراضي في حالة الخطأ

def resolve_full_redirect_chain(link):
    """حل جميع التوجيهات للحصول على الرابط النهائي - نسخة محسنة بشكل جذري"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    try:
        print(f"🔗 بدء حل التوجيهات للرابط: {link}")
        
        session = requests.Session()
        session.headers.update(headers)
        
        # السماح باتباع التوجيهات تلقائياً مع التحكم في العدد
        response = session.get(link, allow_redirects=True, timeout=15, 
                             verify=True, stream=True)
        
        final_url = response.url
        print(f"✅ الرابط النهائي بعد التوجيهات: {final_url}")
        
        # إذا كان الرابط النهائي من star.aliexpress.com، نحتاج لاستخراج redirectUrl
        if "star.aliexpress.com" in final_url:
            print("🔍 اكتشاف رابط star.aliexpress، جاري استخراج redirectUrl...")
            
            # البحث عن redirectUrl في محتوى HTML إذا لم يكن في query parameters
            if 'redirectUrl' not in final_url:
                html_content = response.text
                redirect_match = re.search(r'redirectUrl[=:]\s*["\']([^"\']+)["\']', html_content)
                if redirect_match:
                    redirect_url = redirect_match.group(1)
                    print(f"🔗 وجد redirectUrl في HTML: {redirect_url}")
                    
                    # إصلاح الرابط إذا كان غير مكتمل
                    if redirect_url.startswith('//'):
                        redirect_url = 'https:' + redirect_url
                    elif redirect_url.startswith('/'):
                        redirect_url = 'https://star.aliexpress.com' + redirect_url
                    
                    return resolve_full_redirect_chain(redirect_url)
            
            # إذا كان redirectUrl في query parameters
            parsed_url = urlparse(final_url)
            query_params = parse_qs(parsed_url.query)
            
            if 'redirectUrl' in query_params:
                redirect_url = query_params['redirectUrl'][0]
                print(f"🔗 وجد redirectUrl في query: {redirect_url}")
                
                # فك تشفير URL إذا كان مشفراً
                try:
                    redirect_url = urllib.parse.unquote(redirect_url)
                except:
                    pass
                
                # إصلاح الرابط إذا كان غير مكتمل
                if not redirect_url.startswith('http'):
                    if redirect_url.startswith('//'):
                        redirect_url = 'https:' + redirect_url
                    else:
                        redirect_url = 'https://' + redirect_url
                
                return resolve_full_redirect_chain(redirect_url)
        
        return final_url
        
    except requests.RequestException as e:
        print(f"❌ خطأ في حل التوجيهات للرابط {link}: {e}")
        return link
    except Exception as e:
        print(f"❌ خطأ غير متوقع في حل التوجيهات: {e}")
        return link

def extract_product_id(link):
    """استخراج معرف المنتج من روابط AliExpress المختلفة - نسخة مبسطة وموثوقة"""
    print(f"🔍 جاري استخراج Product ID من: {link}")
    
    try:
        # حل سلسلة التوجيه أولاً
        resolved_link = resolve_full_redirect_chain(link)
        print(f"🔗 الرابط بعد حل التوجيهات: {resolved_link}")
        
        # الأنماط الأساسية الأكثر شيوعاً
        patterns = [
            # النمط الأساسي: /item/1234567890.html
            r'/item/(\d{8,15})\.html',
            # نمط معلمات URL: ?id=1234567890
            r'[?&]id=(\d{8,15})',
            # نمط تطبيق الجوال: /_m/1234567890
            r'/_m/(\d{8,15})',
            # أي رقم طويل في المسار
            r'/(\d{8,15})(?:\.html|/?\?|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, resolved_link)
            if matches:
                product_id = matches[0]
                print(f"✅ تم استخراج ID: {product_id} باستخدام النمط: {pattern}")
                return product_id
        
        # محاولة أخيرة: البحث عن أي رقم طويل في الرابط
        numbers = re.findall(r'\d{9,15}', resolved_link)
        if numbers:
            # تصفية الأرقام الطويلة فقط (عادة product_id بين 8-15 رقم)
            valid_numbers = [n for n in numbers if 8 <= len(n) <= 15]
            if valid_numbers:
                product_id = max(valid_numbers, key=len)
                print(f"✅ تم استخراج ID (أطول رقم مناسب): {product_id}")
                return product_id
        
        print(f"❌ لم أستطع استخراج Product ID من الرابط")
        return None
        
    except Exception as e:
        print(f"❌ خطأ في extract_product_id: {e}")
        return None

def escape_markdown(text):
    """هروب الرموز الخاصة في Markdown لتجنب أخطاء التحليل"""
    if not text:
        return text
    
    # هروب الرموز الخاصة في Markdown
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    
    return text

# Define function to generate affiliate links
def generate_affiliate_links(product_id, original_link):
    """إنشاء جميع الروابط التابعة للمنتج"""
    try:
        affiliate_links = {
            "basic": f"https://ar.aliexpress.com/item/{product_id}.html?aff_fcid={product_id}",
            "coins": f"https://m.aliexpress.com/p/coin-index/index.html?_immersiveMode=true&from=syicon&productIds={product_id}",
            "super": f"https://ar.aliexpress.com/item/{product_id}.html?sourceType=562&aff_fcid={product_id}",
            "limited": f"https://ar.aliexpress.com/item/{product_id}.html?sourceType=561&aff_fcid={product_id}",
            "bundle": f"https://ar.aliexpress.com/item/{product_id}.html?sourceType=560&aff_fcid={product_id}"
        }
        return affiliate_links
    except Exception as e:
        print(f"❌ Error generating affiliate links: {e}")
        return None

# Define function to get enhanced product information
def get_enhanced_product_info(product_id):
    """الحصول على معلومات منتج محسنة مع التخزين المؤقت"""
    # التحقق من التخزين المؤقت أولاً
    cache_key = f"product_{product_id}"
    cached_info = product_cache.get(cache_key)
    if cached_info:
        print(f"✅ Using cached product info for {product_id}")
        return cached_info
    
    try:
        product_details = aliexpress.get_products_details(
            [product_id], 
            fields=[
                "product_title", 
                "target_sale_price", 
                "product_main_image_url",
                "target_original_price",  # السعر الأصلي
                "evaluate_rate",          # التقييم
                "trade_count"            # عدد المبيعات
            ]
        )
        
        if product_details and len(product_details) > 0:
            product = product_details[0]
            
            # حساب التوفير
            original_price = getattr(product, 'target_original_price', None)
            sale_price = getattr(product, 'target_sale_price', 0)
            discount = 0
            if original_price and sale_price and float(original_price) > 0:
                discount = ((float(original_price) - float(sale_price)) / float(original_price)) * 100
            
            product_info = {
                'title': getattr(product, 'product_title', 'غير متوفر'),
                'sale_price': float(sale_price) if sale_price else 0,
                'original_price': float(original_price) if original_price else None,
                'image': getattr(product, 'product_main_image_url', ''),
                'rating': getattr(product, 'evaluate_rate', 'غير متوفر'),
                'sales_count': getattr(product, 'trade_count', 'غير متوفر'),
                'discount': round(discount, 1) if discount > 0 else None
            }
            
            # تخزين في الكاش
            product_cache.set(cache_key, product_info)
            print(f"✅ تم جلب معلومات المنتج وتخزينها في الكاش: {product_id}")
            return product_info
        
        return None
    except Exception as e:
        print(f"❌ Error in get_enhanced_product_info: {e}")
        return None

# Define function to create product message
def create_product_message(product_info, affiliate_links):
    """إنشاء رسالة منتج محسنة - بدون Markdown"""
    price_pro = product_info['sale_price']
    exchange_rate = get_usd_to_mad_rate()
    price_pro_mad = price_pro * exchange_rate if exchange_rate else price_pro
    
    # هروب النص لتجنب مشاكل Markdown
    safe_title = escape_markdown(product_info['title'])
    safe_rating = escape_markdown(str(product_info['rating']))
    safe_sales_count = escape_markdown(str(product_info['sales_count']))
    
    message_parts = [
        f"🛒 {safe_title} 🛍",
        f"⭐️ التقييم: {safe_rating}",
        f"🛍 المبيعات: {safe_sales_count}",
        "",
        f"💰 السعر:",
        f"• ${price_pro:.2f} ≈ {price_pro_mad:.2f} درهم"
    ]
    
    # إضافة السعر الأصلي والتوفير إذا متوفر
    if product_info['original_price'] and product_info['original_price'] > price_pro:
        original_mad = product_info['original_price'] * exchange_rate if exchange_rate else product_info['original_price']
        message_parts.extend([
            f"• ~~${product_info['original_price']:.2f}~~ ← وفر {product_info['discount']}%",
            f"• ~~{original_mad:.2f} درهم~~"
        ])
    
    message_parts.extend([
        "",
        "🔗 اختر طريقة الشراء:",
        "",
        f"🛒 رابط الشراء الأساسي:",
        f"{affiliate_links['basic']}",
        "",
        f"💰 صفحة العملات:", 
        f"{affiliate_links['coins']}",
        "",
        f"💎 عروض خاصة:",
        f"• عرض السوبر: {affiliate_links['super']}",
        f"• عرض محدود: {affiliate_links['limited']}",
        f"• عرض الحزمة: {affiliate_links['bundle']}",
        "",
        "#AliExpressSaverBot 🎯"
    ])
    
    return "\n".join(message_parts)

# Define function to create simple product message (بدون تنسيق)
def create_simple_product_message(product_info, affiliate_links):
    """إنشاء رسالة منتج بسيطة بدون أي تنسيق Markdown"""
    price_pro = product_info['sale_price']
    exchange_rate = get_usd_to_mad_rate()
    price_pro_mad = price_pro * exchange_rate if exchange_rate else price_pro
    
    message = f"""🛒 {product_info['title']} 🛍
⭐️ التقييم: {product_info['rating']}
🛍 المبيعات: {product_info['sales_count']}

💰 السعر:
• ${price_pro:.2f} ≈ {price_pro_mad:.2f} درهم
"""

    # إضافة السعر الأصلي والتوفير إذا متوفر
    if product_info['original_price'] and product_info['original_price'] > price_pro:
        original_mad = product_info['original_price'] * exchange_rate if exchange_rate else product_info['original_price']
        message += f"• ~~${product_info['original_price']:.2f}~~ ← وفر {product_info['discount']}%\n"
        message += f"• ~~{original_mad:.2f} درهم~~\n\n"

    message += f"""🔗 اختر طريقة الشراء:

🛒 رابط الشراء الأساسي:
{affiliate_links['basic']}

💰 صفحة العملات:
{affiliate_links['coins']}

💎 عروض خاصة:
• عرض السوبر: {affiliate_links['super']}
• عرض محدود: {affiliate_links['limited']}
• عرض الحزمة: {affiliate_links['bundle']}

#AliExpressSaverBot 🎯"""
    
    return message

# Define function to analyze link type
def analyze_link_type(link):
    """تحليل نوع الرابط"""
    if 'shoppingcart' in link.lower():
        return 'shopcart'
    elif 'coin' in link.lower():
        return 'coin'
    elif 'game' in link.lower() or any(game in link.lower() for game in ['merge', 'farm', 'flip', 'gogo']):
        return 'game'
    elif 'item' in link.lower() or 'product' in link.lower() or 'aliexpress.com' in link.lower():
        return 'product'
    else:
        return 'unknown'

# Define function to safely delete messages
def safe_delete_message(bot, chat_id, message_id):
    """حذف آمن للرسائل"""
    try:
        bot.delete_message(chat_id, message_id)
        return True
    except Exception as e:
        print(f"⚠️ لا يمكن حذف الرسالة {message_id}: {e}")
        return False

# Define function to send error messages
def send_error_message(bot, chat_id, error_type, original_link=None):
    """إرسال رسائل خطأ مخصصة"""
    error_messages = {
        'invalid_link': "❌ الرابط غير صحيح! تأكد من رابط المنتج.",
        'no_product_id': "❌ لم أستطع تحديد المنتج من الرابط. حاول استخدام رابط مباشر من AliExpress.",
        'api_error': "⚠️ حدث خطأ في الخدمة. حاول مرة أخرى.",
        'timeout': "⏰ انتهت المهلة. حاول مرة أخرى.",
        'general': "❌ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
    }
    
    message = error_messages.get(error_type, "حدث خطأ غير متوقع")
    if original_link:
        message += f"\n\n🔗 الرابط المرسل:\n{original_link}"
    
    bot.send_message(chat_id, message)

# Define bot handlers
@bot.message_handler(commands=['start'])
def welcome_user(message):
    print("Handling /start command")
    bot.send_message(
        message.chat.id,
        "مرحبا بكم👋 \n" 
        "أنا علي إكسبريس بوت أقوم بتخفيض المنتجات و البحث  عن أفضل العروض إنسخ رابط المنتج وضعه هنا 👇 ستجد جميع عروض المنتج بثمن أقل 🔥",
        reply_markup=keyboardStart)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        print(f"📩 Message received: {message.text}")
        link = extract_link(message.text)
        
        if not link:
            bot.send_message(message.chat.id, "❌ لم أتمكن من العثور على رابط في رسالتك.")
            return
            
        # تحليل نوع الرابط
        link_type = analyze_link_type(link)
        print(f"🔍 Link type: {link_type}")
        
        sent_message = bot.send_message(message.chat.id, '⏳ المرجو الانتظار قليلا، يتم تجهيز العروض...')
        message_id = sent_message.message_id
        
        if link_type == 'shopcart':
            get_affiliate_shopcart_link(link, message, message_id)
        elif link_type == 'product':
            get_affiliate_links(message, message_id, link)
        elif link_type == 'game':
            handle_game_link(message, message_id)
        else:
            safe_delete_message(bot, message.chat.id, message_id)
            send_error_message(bot, message.chat.id, 'invalid_link', link)
            
    except Exception as e:
        print(f"❌ Error in echo_all handler: {e}")
        send_error_message(bot, message.chat.id, 'general')

def extract_link(text):
    """استخراج الروابط من النص"""
    link_pattern = r'https?://[^\s]+|www\.[^\s]+'
    links = re.findall(link_pattern, text)
    if links:
        print(f"🔗 Extracted link: {links[0]}")
        return links[0]
    return None

def get_affiliate_links(message, message_id, link):
    """معالجة روابط المنتجات - نسخة آمنة بدون Markdown"""
    try:
        print(f"🔗 معالجة الرابط: {link}")
        
        # حل سلسلة التوجيه أولاً
        resolved_link = resolve_full_redirect_chain(link)
        if not resolved_link:
            safe_delete_message(bot, message.chat.id, message_id)
            send_error_message(bot, message.chat.id, 'invalid_link', link)
            return

        print(f"✅ الرابط النهائي: {resolved_link}")

        # استخرج معرف المنتج من الرابط المحلول
        product_id = extract_product_id(resolved_link)
        if not product_id:
            safe_delete_message(bot, message.chat.id, message_id)
            
            # عرض معلومات مفصلة للمساعدة في التصحيح
            debug_info = (
                f"❌ لم أستطع تحديد معرف المنتج من الرابط\n\n"
                f"🔗 الرابط الأصلي:\n{link}\n\n"
                f"🔗 الرابط بعد التوجيهات:\n{resolved_link}\n\n"
                f"💡 الحلول المقترحة:\n"
                f"• تأكد من أن الرابط من موقع AliExpress الرسمي\n"
                f"• حاول استخدام رابط مباشر من صفحة المنتج\n"
                f"• تجنب روابط التطبيقات أو الروابط القصيرة"
            )
            bot.send_message(message.chat.id, debug_info)
            return

        print(f"🎯 معالجة المنتج ID: {product_id}")

        # إنشاء روابط تابعة
        affiliate_links = generate_affiliate_links(product_id, resolved_link)
        if not affiliate_links:
            safe_delete_message(bot, message.chat.id, message_id)
            send_error_message(bot, message.chat.id, 'api_error')
            return

        # الحصول على معلومات المنتج
        product_info = get_enhanced_product_info(product_id)
        
        safe_delete_message(bot, message.chat.id, message_id)
        
        if product_info and product_info.get('image'):
            try:
                # المحاولة الأولى: استخدام تنسيق آمن
                message_text = create_simple_product_message(product_info, affiliate_links)
                bot.send_photo(
                    message.chat.id,
                    product_info['image'],
                    caption=message_text,
                    reply_markup=keyboard
                    # لا نستخدم parse_mode لتجنب مشاكل Markdown
                )
            except Exception as e:
                print(f"⚠️ Error with photo message, trying text only: {e}")
                # إذا فشلت المحاولة الأولى، جرب بدون صورة
                try:
                    message_text = create_simple_product_message(product_info, affiliate_links)
                    bot.send_message(
                        message.chat.id,
                        message_text,
                        reply_markup=keyboard
                    )
                except Exception as e2:
                    print(f"❌ Error with text message: {e2}")
                    # آخر محاولة: رسالة بسيطة جداً
                    simple_message = f"🛒 {product_info['title'][:100]}...\n\n"
                    simple_message += f"💰 السعر: ${product_info['sale_price']:.2f}\n\n"
                    simple_message += f"🔗 روابط الشراء:\n{affiliate_links['basic']}"
                    bot.send_message(message.chat.id, simple_message, reply_markup=keyboard)
        else:
            # Fallback إذا لم تكن هناك معلومات منتج
            message_text = (
                f"🔗 اختر طريقة الشراء:\n\n"
                f"🛒 رابط الشراء الأساسي:\n{affiliate_links['basic']}\n\n"
                f"💰 صفحة العملات:\n{affiliate_links['coins']}\n\n"
                f"💎 عروض خاصة:\n"
                f"• عرض السوبر: {affiliate_links['super']}\n"
                f"• عرض محدود: {affiliate_links['limited']}\n"
                f"• عرض الحزمة: {affiliate_links['bundle']}\n\n"
                f"#AliExpressSaverBot 🎯"
            )
            bot.send_message(
                message.chat.id,
                message_text,
                reply_markup=keyboard
            )
            
    except Exception as e:
        print(f"❌ Error in get_affiliate_links: {e}")
        safe_delete_message(bot, message.chat.id, message_id)
        send_error_message(bot, message.chat.id, 'general')

def handle_game_link(message, message_id):
    """معالجة روابط الألعاب"""
    safe_delete_message(bot, message.chat.id, message_id)
    img_link2 = "https://i.postimg.cc/VvmhgQ1h/Basket-aliexpress-telegram.png"
    bot.send_photo(
        message.chat.id,
        img_link2,
        caption="🎮 روابط ألعاب جمع العملات المعدنية\n\n"
                "استعمل هذه الألعاب يومياً لجمع أكبر عدد ممكن من العملات\n"
                "ثم استخدمها في خفض أسعار المنتجات في سلة التسوق 👇",
        reply_markup=keyboard_games
    )

def build_shopcart_link(link):
    """بناء رابط سلة التسوق"""
    params = get_url_params(link)
    shop_cart_link = "https://www.aliexpress.com/p/trade/confirm.html?"
    shop_cart_params = {
        "availableProductShopcartIds": ",".join(params["availableProductShopcartIds"]),
        "extraParams": json.dumps({"channelInfo": {"sourceType": "620"}}, separators=(',', ':'))
    }
    return create_query_string_url(link=shop_cart_link, params=shop_cart_params)

def get_url_params(link):
    """استخراج معلمات URL"""
    parsed_url = urlparse(link)
    params = parse_qs(parsed_url.query)
    return params

def create_query_string_url(link, params):
    """إنشاء رابط مع معلمات query"""
    return link + urllib.parse.urlencode(params, doseq=True)

def get_affiliate_shopcart_link(link, message, message_id):
    """معالجة روابط سلة التسوق"""
    try:
        shopcart_link = build_shopcart_link(link)
        affiliate_links = aliexpress.get_affiliate_links(shopcart_link)
        
        if affiliate_links and len(affiliate_links) > 0:
            affiliate_link = affiliate_links[0].promotion_link
            safe_delete_message(bot, message.chat.id, message_id)
            
            text2 = (
                "🛒 رابط تخفيض سلة التسوق\n\n"
                f"{affiliate_link}\n\n"
                "⚠️ ملاحظة: استخدم هذا الرابط للاستفادة من التخفيضات على منتجات سلة التسوق"
            )
            img_link3 = "https://i.postimg.cc/1Xrk1RJP/Copy-of-Basket-aliexpress-telegram.png"
            
            bot.send_photo(
                message.chat.id, 
                img_link3, 
                caption=text2
            )
        else:
            safe_delete_message(bot, message.chat.id, message_id)
            send_error_message(bot, message.chat.id, 'api_error')
            
    except Exception as e:
        print(f"❌ Error in get_affiliate_shopcart_link: {e}")
        safe_delete_message(bot, message.chat.id, message_id)
        send_error_message(bot, message.chat.id, 'general')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        print(f"🔘 Callback query received: {call.data}")
        if call.data == 'click':
            link = 'https://www.aliexpress.com/p/shoppingcart/index.html?'
            sent_message = bot.send_message(call.message.chat.id, '⏳ جاري تجهيز رابط سلة التسوق...')
            get_affiliate_shopcart_link(link, call.message, sent_message.message_id)
        else:
            bot.answer_callback_query(call.id, "⚠️ الأمر غير معروف")
            
    except Exception as e:
        print(f"❌ Error in handle_callback_query: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ في المعالجة")

# Flask app for handling webhook
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK', 200

@app.route('/health', methods=['GET'])
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200

if __name__ == "__main__":
    # استخدم POLLING مباشرة - لا حاجة لـ Webhook
    print("🚀 Starting bot in POLLING mode...")
    
    # تأكد من إزالة أي Webhook سابق
    try:
        bot.remove_webhook()
        print("✅ Cleaned any existing webhooks")
    except Exception as e:
        print(f"⚠️ Error removing webhook: {e}")
    
    # ابدأ Polling مباشرة
    print("🔄 Bot is running and waiting for messages...")
    
    try:
        bot.infinity_polling(
            none_stop=True,
            timeout=60,
            long_polling_timeout=45,
            skip_pending=True
        )
    except Exception as e:
        print(f"❌ Polling error: {e}")
