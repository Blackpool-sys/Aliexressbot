import json
import telebot
from flask import Flask, request
import threading
from telebot import types
import re
import os
from urllib.parse import urlparse, parse_qs, quote_plus
import urllib.parse
import requests

# Load environment variables
TELEGRAM_TOKEN_BOT = os.getenv('TELEGRAM_TOKEN_BOT')
ALIEXPRESS_API_PUBLIC = os.getenv('ALIEXPRESS_API_PUBLIC')
ALIEXPRESS_API_SECRET = os.getenv('ALIEXPRESS_API_SECRET')

# التحقق من التوكن الأساسي فقط - لا تتوقف إذا لم توجد مفاتيح API
if not TELEGRAM_TOKEN_BOT:
    print("X Error: TELEGRAM_TOKEN_BOT environment variable is not set!")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN_BOT)

# Initialize Aliexpress API إذا كانت المفاتيح موجودة
aliexpress = None
if ALIEXPRESS_API_PUBLIC and ALIEXPRESS_API_SECRET:
    try:
        from aliexpress_api import AliexpressApi, models
        aliexpress = AliexpressApi(ALIEXPRESS_API_PUBLIC, ALIEXPRESS_API_SECRET,
                                   models.Language.AR, models.Currency.EUR, 'telegrame_bot')
        print("✅ AliExpress API initialized successfully.")
    except Exception as e:
        print(f"⚠️ AliExpress API initialization failed: {e}")
        print("🔧 Continuing with direct links only")
        aliexpress = None
else:
    print("⚠️ AliExpress API keys not set, using direct links only")

print("🤖 Telegram Bot started successfully!")

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
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        data = response.json()
        return data['rates']['MAD']
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return 10.0  # سعر افتراضي

# Define function to resolve redirect chain and get final URL
def resolve_full_redirect_chain(link):
    """حل جميع التوجيهات للحصول على الرابط النهائي"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        session_req = requests.Session()
        response = session_req.get(link, allow_redirects=True, timeout=8, headers=headers)
        final_url = response.url
        print(f"🔗 Resolved URL: {link} -> {final_url}")
        
        if "star.aliexpress.com" in final_url:
            parsed_url = urlparse(final_url)
            params = parse_qs(parsed_url.query)
            if 'redirectUrl' in params:
                redirect_url = params['redirectUrl'][0]
                print(f"🔗 Found redirectUrl: {redirect_url}")
                if not redirect_url.startswith('http'):
                    redirect_url = 'https:' + redirect_url
                return resolve_full_redirect_chain(redirect_url)
        
        return final_url
        
    except requests.RequestException as e:
        print(f"❌ Error resolving redirect chain: {e}")
        return link

# Define function to extract product ID from link
def extract_product_id(link):
    """استخراج معرف المنتج من روابط AliExpress المختلفة"""
    print(f"🔍 Extracting product ID from: {link}")
    
    try:
        resolved_link = resolve_full_redirect_chain(link)
        print(f"🔗 Using resolved link: {resolved_link}")
        
        patterns = [
            r'/item/(\d+)\.html',
            r'/item/(\d{10,})\.html',
            r'/item/(\d{10,})(?:\?|$)',
            r'productIds=(\d+)',
            r'/(\d{10,})(?:\.html|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, resolved_link)
            if match:
                product_id = match.group(1)
                print(f"✅ Extracted product ID: {product_id}")
                return product_id
        
        numbers = re.findall(r'\d{9,}', resolved_link)
        if numbers:
            product_id = max(numbers, key=len)
            print(f"✅ Extracted product ID (longest number): {product_id}")
            return product_id
        
        print(f"❌ Could not extract product ID")
        return None
        
    except Exception as e:
        print(f"❌ Error in extract_product_id: {e}")
        return None

# Define function to generate coin-index affiliate link for 620 channel
def generate_coin_affiliate_link(product_id):
    """إنشاء رابط تابع باستخدام نظام coin-index للقناة 620"""
    if not aliexpress:
        return f"https://m.aliexpress.com/p/coin-index/index.html?_immersiveMode=true&from=syicon&productIds={product_id}"
    
    try:
        coin_index_url = f"https://m.aliexpress.com/p/coin-index/index.html?_immersiveMode=true&from=syicon&productIds={product_id}"
        affiliate_links = aliexpress.get_affiliate_links(coin_index_url)
        if affiliate_links and len(affiliate_links) > 0:
            return affiliate_links[0].promotion_link
        return coin_index_url
    except Exception as e:
        print(f"❌ Error generating coin affiliate link: {e}")
        return f"https://m.aliexpress.com/p/coin-index/index.html?_immersiveMode=true&from=syicon&productIds={product_id}"

# Define function to generate bundle affiliate link for 560 channel
def generate_bundle_affiliate_link(product_id, original_link):
    """إنشاء رابط تابع باستخدام نظام bundle للقناة 560"""
    try:
        encoded_url = quote_plus(original_link)
        bundle_url = f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType=560'
        
        if aliexpress:
            affiliate_links = aliexpress.get_affiliate_links(bundle_url)
            if affiliate_links and len(affiliate_links) > 0:
                return affiliate_links[0].promotion_link
        
        return bundle_url
    except Exception as e:
        print(f"❌ Error generating bundle affiliate link: {e}")
        encoded_url = quote_plus(original_link)
        return f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType=560'

# Define function to generate other affiliate links
def generate_other_links(resolved_link, source_type):
    """إنشاء روابط أخرى"""
    try:
        if aliexpress:
            affiliate_links = aliexpress.get_affiliate_links(
                f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={resolved_link}?sourceType={source_type}'
            )
            if affiliate_links and len(affiliate_links) > 0:
                return affiliate_links[0].promotion_link
        
        # Fallback to direct link
        encoded_url = quote_plus(resolved_link)
        return f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType={source_type}'
    except Exception as e:
        print(f"❌ Error generating link for source {source_type}: {e}")
        encoded_url = quote_plus(resolved_link)
        return f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType={source_type}'

# Define bot handlers
@bot.message_handler(commands=['start'])
def welcome_user(message):
    print("Handling /start command")
    bot.send_message(
        message.chat.id,
        "مرحبا بكم👋 \n" 
        "أنا علي إكسبريس بوت أقوم بتخفيض المنتجات و البحث عن أفضل العروض إنسخ رابط المنتج وضعه هنا 👇 ستجد جميع عروض المنتج بثمن أقل 🔥",
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
            bot.send_message(message.chat.id, "الرابط غير صحيح ! تأكد من رابط المنتج أو اعد المحاولة.\n قم بإرسال <b> الرابط فقط</b> بدون عنوان المنتج", parse_mode='HTML')
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
        resolved_link = resolve_full_redirect_chain(link)
        if not resolved_link:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, "❌ لم أتمكن من حل الرابط! تأكد من رابط المنتج أو أعد المحاولة.")
            return

        product_id = extract_product_id(resolved_link)
        if not product_id:
            bot.delete_message(message.chat.id, message_id)
            bot.send_message(message.chat.id, f"❌ لم أتمكن من استخراج معرف المنتج من الرابط.")
            return

        print(f"🎯 Processing product ID: {product_id}")

        # Generate all affiliate links
        coin_affiliate_link = generate_coin_affiliate_link(product_id)
        bundle_affiliate_link = generate_bundle_affiliate_link(product_id, resolved_link)
        super_links = generate_other_links(resolved_link, '562')
        limit_links = generate_other_links(resolved_link, '561')

        # Try to get product details
        product_title = "منتج AliExpress"
        product_price = 0.0
        product_image = "https://via.placeholder.com/300x300?text=Product+Image"
        
        if aliexpress:
            try:
                product_details = aliexpress.get_products_details(
                    [product_id], 
                    fields=["target_sale_price", "product_title", "product_main_image_url"]
                )
                
                if product_details and len(product_details) > 0:
                    product_price = float(product_details[0].target_sale_price)
                    product_title = product_details[0].product_title
                    product_image = product_details[0].product_main_image_url
            except Exception as e:
                print(f"⚠️ Could not fetch product details: {e}")

        # Convert price to MAD
        exchange_rate = get_usd_to_mad_rate()
        price_pro_mad = product_price * exchange_rate

        # Build the message
        message_text = f"""
🛒 منتجك هو : 🔥 
{product_title} 🛍 
سعر المنتج : {product_price:.2f} دولار 💵 / {price_pro_mad:.2f} درهم مغربي 💵

قارن بين الاسعار واشتري 🔥

💰 عرض العملات (السعر النهائي عند الدفع) :
{coin_affiliate_link}

📦 عرض الحزمة (عروض متنوعة) :
{bundle_affiliate_link}

💎 عرض السوبر :
{super_links}

🔥 عرض محدود :
{limit_links}

#AliExpressSaverBot ✅
"""
        
        bot.delete_message(message.chat.id, message_id)
        bot.send_photo(message.chat.id, product_image, caption=message_text, reply_markup=keyboard)
        
    except Exception as e:
        print(f"Error in get_affiliate_links: {e}")
        bot.send_message(message.chat.id, "حدث خطأ 🤷🏻‍♂️")

def get_affiliate_shopcart_link(link, message):
    try:
        if aliexpress:
            shopcart_link = build_shopcart_link(link)
            affiliate_link = aliexpress.get_affiliate_links(shopcart_link)[0].promotion_link
            text2 = f"هذا رابط تخفيض السلة \n{str(affiliate_link)}"
        else:
            text2 = f"هذا رابط تخفيض السلة \n{link}"
            
        img_link3 = "https://i.postimg.cc/1Xrk1RJP/Copy-of-Basket-aliexpress-telegram.png"
        bot.send_photo(message.chat.id, img_link3, caption=text2)
    except Exception as e:
        print(f"Error in get_affiliate_shopcart_link: {e}")
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

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        print(f"Callback query received: {call.data}")
        if call.data == 'click':
            link = 'https://www.aliexpress.com/p/shoppingcart/index.html?'
            get_affiliate_shopcart_link(link, call.message)
        else:
            img_link2 = "https://i.postimg.cc/VvmhgQ1h/Basket-aliexpress-telegram.png"
            bot.send_photo(call.message.chat.id, img_link2,
                           caption="روابط ألعاب جمع العملات المعدنية لإستعمالها في خفض السعر لبعض المنتجات، قم بالدخول يوميا لها للحصول على أكبر عدد ممكن في اليوم 👇",
                           reply_markup=keyboard_games)
    except Exception as e:
        print(f"Error in handle_callback_query: {e}")

# Flask app for handling webhook
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 AliExpress Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return 'OK', 200

if __name__ == "__main__":
    # على Render، استخدم webhook دائماً
    print("🚀 Starting bot on Render...")
    
    webhook_url = os.getenv('RENDER_EXTERNAL_URL') or os.getenv('WEBHOOK_URL')
    
    if webhook_url:
        print("🌐 Production mode: Using webhook")
        threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000)).start()
        try:
            bot.remove_webhook()
            bot.set_webhook(url=f"{webhook_url}/webhook")
            print(f"✅ Webhook set to: {webhook_url}/webhook")
        except Exception as e:
            print(f"❌ Error setting webhook: {e}")
    else:
        print("🔧 Development mode: Using polling")
        bot.infinity_polling()
