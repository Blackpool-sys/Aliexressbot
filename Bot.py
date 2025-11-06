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

# Define function to get exchange rate from USD to MAD
def get_usd_to_mad_rate():
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        data = response.json()
        return data['rates']['MAD']
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

# Define function to resolve redirect chain and get final URL
def resolve_full_redirect_chain(link):
    """حل جميع التوجيهات للحصول على الرابط النهائي"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.36'
    }
    try:
        session_req = requests.Session()
        response = session_req.get(link, allow_redirects=True, timeout=10, headers=headers)
        final_url = response.url
        print(f"🔗 Resolved URL: {link} -> {final_url}")
        
        # إذا كان رابط star.aliexpress، استخرج redirectUrl
        if "star.aliexpress.com" in final_url:
            parsed_url = urlparse(final_url)
            params = parse_qs(parsed_url.query)
            if 'redirectUrl' in params:
                redirect_url = params['redirectUrl'][0]
                print(f"🔗 Found redirectUrl: {redirect_url}")
                # حل التوجيه مرة أخرى إذا لزم الأمر
                if not redirect_url.startswith('http'):
                    redirect_url = 'https:' + redirect_url
                return resolve_full_redirect_chain(redirect_url)
        
        return final_url
        
    except requests.RequestException as e:
        print(f"❌ Error resolving redirect chain for link {link}: {e}")
        return link  # ارجع للرابط الأصلي إذا فشل الحل

# Define function to extract product ID from link
def extract_product_id(link):
    """استخراج معرف المنتج من روابط AliExpress المختلفة"""
    print(f"🔍 Extracting product ID from: {link}")
    
    try:
        # First resolve any redirects to get the final URL
        resolved_link = resolve_full_redirect_chain(link)
        print(f"🔗 Using resolved link: {resolved_link}")
        
        # قائمة بأنماط الروابط المختلفة
        patterns = [
            # النمط الأساسي: /item/1234567890.html
            r'/item/(\d+)\.html',
            # نمط المنتج الطويل: /item/1005001234567890.html
            r'/item/(\d{10,})\.html',
            # نمط بدون .html: /item/1234567890
            r'/item/(\d{10,})(?:\?|$)',
            # نمط coin-index: productIds=1234567890
            r'productIds=(\d+)',
            # نمط تطبيق الجوال: /_m/1234567890
            r'/_m/(\d+)',
            # نمط المنتج البديل: /product/1234567890.html
            r'/product/(\d+)\.html',
            # أي رقم طويل في الرابط
            r'/(\d{10,})(?:\.html|$)',
            # نمط من query parameters
            r'[?&]id=(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, resolved_link)
            if match:
                product_id = match.group(1)
                print(f"✅ Extracted product ID using pattern '{pattern}': {product_id}")
                return product_id
        
        # إذا فشلت جميع الأنماط، جرب البحث عن أي رقم طويل
        numbers = re.findall(r'\d{9,}', resolved_link)
        if numbers:
            # خذ أطول رقم (غالباً هو product_id)
            product_id = max(numbers, key=len)
            print(f"✅ Extracted product ID (longest number): {product_id}")
            return product_id
        
        print(f"❌ Could not extract product ID from: {resolved_link}")
        return None
        
    except Exception as e:
        print(f"❌ Error in extract_product_id: {e}")
        return None

# Define function to generate coin-index affiliate link for 620 channel
def generate_coin_affiliate_link(product_id):
    """إنشاء رابط تابع باستخدام نظام coin-index للقناة 620"""
    try:
        # أنشئ رابط coin-index
        coin_index_url = f"https://m.aliexpress.com/p/coin-index/index.html?_immersiveMode=true&from=syicon&productIds={product_id}"
        
        # أنشئ الرابط التابع
        affiliate_links = aliexpress.get_affiliate_links(coin_index_url)
        if affiliate_links and len(affiliate_links) > 0:
            return affiliate_links[0].promotion_link
        return None
    except Exception as e:
        print(f"❌ Error generating coin affiliate link for product {product_id}: {e}")
        return None

# Define function to generate bundle affiliate link for 560 channel
def generate_bundle_affiliate_link(product_id, original_link):
    """إنشاء رابط تابع باستخدام نظام bundle للقناة 560"""
    try:
        # تشفير الرابط الأصلي
        encoded_url = urllib.parse.quote_plus(original_link)
        # أنشئ رابط bundle
        bundle_url = f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType=560'
        
        # أنشئ الرابط التابع
        affiliate_links = aliexpress.get_affiliate_links(bundle_url)
        if affiliate_links and len(affiliate_links) > 0:
            return affiliate_links[0].promotion_link
        return None
    except Exception as e:
        print(f"⚠️ Bundle links temporarily disabled - IP not whitelisted")
        return None

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
        print(f"Message received: {message.text}")
        link = extract_link(message.text)
        sent_message = bot.send_message(message.chat.id, 'المرجو الانتظار قليلا، يتم تجهيز العروض ⏳')
        message_id = sent_message.message_id
        if link and "aliexpress.com" in link and not ("p/shoppingcart" in message.text.lower()):
            if "availableProductShopcartIds".lower() in message.text.lower():
                get_affiliate_shopcart_link(link, message)
                return
            get_affiliate_links(message, message_id, link)
        else:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, "الرابط غير صحيح ! تأكد من رابط المنتج أو اعد المحاولة.\n"
                                              " قم بإرسال <b> الرابط فقط</b> بدون عنوان المنتج",
                             parse_mode='HTML')
    except Exception as e:
        print(f"Error in echo_all handler: {e}")

def extract_link(text):
    link_pattern = r'https?://\S+|www\.\S+'
    links = re.findall(link_pattern, text)
    if links:
        print(f"Extracted link: {links[0]}")
        return links[0]
    return None

def get_affiliate_links(message, message_id, link):
    try:
        # حل سلسلة التوجيه أولاً
        resolved_link = resolve_full_redirect_chain(link)
        if not resolved_link:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, "❌ لم أتمكن من حل الرابط! تأكد من رابط المنتج أو أعد المحاولة.")
            return

        # استخرج معرف المنتج من الرابط المحلول
        product_id = extract_product_id(resolved_link)
        if not product_id:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, f"❌ لم أتمكن من استخراج معرف المنتج من الرابط.\nالرابط: {resolved_link}")
            return

        print(f"🎯 Processing product ID: {product_id}")

        # إنشاء روابط تابعة مباشرة (بدون استخدام API)
        affiliate_links = {
            "🛒 رابط الشراء الأساسي": f"https://ar.aliexpress.com/item/{product_id}.html?aff_fcid={product_id}",
            "💰 صفحة العملات": f"https://m.aliexpress.com/p/coin-index/index.html?_immersiveMode=true&from=syicon&productIds={product_id}",
            "💎 عرض السوبر": f"https://ar.aliexpress.com/item/{product_id}.html?sourceType=562&aff_fcid={product_id}",
            "🔥 عرض محدود": f"https://ar.aliexpress.com/item/{product_id}.html?sourceType=561&aff_fcid={product_id}",
            "📦 عرض الحزمة": f"https://ar.aliexpress.com/item/{product_id}.html?sourceType=560&aff_fcid={product_id}"
        }

        try:
            # Get product details using the product ID
            product_details = aliexpress.get_products_details([
                product_id
            ], fields=["target_sale_price", "product_title", "product_main_image_url"])
            
            if product_details and len(product_details) > 0:
                price_pro = float(product_details[0].target_sale_price)
                title_link = product_details[0].product_title
                img_link = product_details[0].product_main_image_url
                
                # Convert price to MAD
                exchange_rate = get_usd_to_mad_rate()
                if exchange_rate:
                    price_pro_mad = price_pro * exchange_rate
                else:
                    price_pro_mad = price_pro
                
                print(f"Product details: {title_link}, {price_pro}, {img_link}")
                bot.delete_message(message.chat.id, message_id)
                
                # Build the message with all affiliate links
                message_text = (
                    f"🛒 **{title_link}** 🛍\n"
                    f"💰 السعر: {price_pro:.2f}$ / {price_pro_mad:.2f} درهم\n\n"
                    f"🔗 **اختر طريقة الشراء:**\n"
                )
                
                # إضافة جميع الروابط
                for link_name, link_url in affiliate_links.items():
                    message_text += f"\n{link_name}:\n{link_url}\n"
                
                message_text += "\n#AliExpressSaverBot ✅"
                
                bot.send_photo(message.chat.id,
                               img_link,
                               caption=message_text,
                               reply_markup=keyboard,
                               parse_mode='Markdown')
            else:
                # Fallback if product details couldn't be fetched
                bot.delete_message(message.chat.id, message_id)
                
                message_text = "🔗 **اختر طريقة الشراء:**\n"
                
                for link_name, link_url in affiliate_links.items():
                    message_text += f"\n{link_name}:\n{link_url}\n"
                
                message_text += "\n#AliExpressSaverBot ✅"
                
                bot.send_message(message.chat.id, message_text, reply_markup=keyboard, parse_mode='Markdown')
                
        except Exception as e:
            print(f"Error in get_affiliate_links inner try: {e}")
            bot.delete_message(message.chat.id, message_id)
            
            # Fallback with just links
            message_text = "🔗 **اختر طريقة الشراء:**\n"
            
            for link_name, link_url in affiliate_links.items():
                message_text += f"\n{link_name}:\n{link_url}\n"
            
            message_text += "\n#AliExpressSaverBot ✅"
            
            bot.send_message(message.chat.id, message_text, reply_markup=keyboard, parse_mode='Markdown')
            
    except Exception as e:
        print(f"Error in get_affiliate_links: {e}")
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

def build_shopcart_link(link):
    params = get_url_params(link)
    shop_cart_link = "https://www.aliexpress.com/p/trade/confirm.html?"
    shop_cart_params = {
        "availableProductShopcartIds": ",".join(params["availableProductShopcartIds"]),
        "extraParams": json.dumps({"channelInfo": {"sourceType": "620"}}, separators=(',', ':'))
    }
    return create_query_string_url(link=shop_cart_link, params=shop_cart_params)

def get_url_params(link):
    parsed_url = urlparse(link)
    params = parse_qs(parsed_url.query)
    return params

def create_query_string_url(link, params):
    return link + urllib.parse.urlencode(params)

def get_affiliate_shopcart_link(link, message):
    try:
        shopcart_link = build_shopcart_link(link)
        affiliate_link = aliexpress.get_affiliate_links(shopcart_link)[0].promotion_link
        text2 = f"هذا رابط تخفيض السلة \n{str(affiliate_link)}"
        img_link3 = "https://i.postimg.cc/1Xrk1RJP/Copy-of-Basket-aliexpress-telegram.png"
        bot.send_photo(message.chat.id, img_link3, caption=text2)
    except Exception as e:
        print(f"Error in get_affiliate_shopcart_link: {e}")
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        print(f"Callback query received: {call.data}")
        if call.data == 'click':
            # Replace with your link and message if needed
            link = 'https://www.aliexpress.com/p/shoppingcart/index.html?'
            get_affiliate_shopcart_link(link, call.message)
        else:
            bot.send_message(call.message.chat.id, "..")
            img_link2 = "https://i.postimg.cc/VvmhgQ1h/Basket-aliexpress-telegram.png"
            bot.send_photo(call.message.chat.id,
                           img_link2,
                           caption="روابط ألعاب جمع العملات المعدنية لإستعمالها في خفض السعر لبعض المنتجات، قم بالدخول يوميا لها للحصول على أكبر عدد ممكن في اليوم 👇",
                           reply_markup=keyboard_games)
    except Exception as e:
        print(f"Error in handle_callback_query: {e}")

# Flask app for handling webhook
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK', 200

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
