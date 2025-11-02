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

# Load environment variables - استخدام أسماء متغيرات صحيحة
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALIEXPRESS_API_PUBLIC = os.getenv('ALIEXPRESS_API_PUBLIC')
ALIEXPRESS_API_SECRET = os.getenv('ALIEXPRESS_API_SECRET')

# تحقق من التوكن فقط
if not TELEGRAM_BOT_TOKEN:
    print("X Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
    print("Please add TELEGRAM_BOT_TOKEN to your Render environment variables")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
print("✅ Telegram Bot initialized successfully")

# Initialize Aliexpress API إذا كانت المفاتيح موجودة
aliexpress = None
if ALIEXPRESS_API_PUBLIC and ALIEXPRESS_API_SECRET:
    try:
        from aliexpress_api import AliexpressApi, models
        aliexpress = AliexpressApi(ALIEXPRESS_API_PUBLIC, ALIEXPRESS_API_SECRET,
                                   models.Language.AR, models.Currency.EUR, 'telegram_bot')
        print("✅ AliExpress API initialized successfully.")
    except Exception as e:
        print(f"⚠️ AliExpress API failed: {e}")
        aliexpress = None
else:
    print("⚠️ AliExpress API keys not set, using direct links")

# Keyboards (نفس الكيبوردز السابقة)
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

# دالة استخراج product_id مبسطة
def extract_product_id(link):
    try:
        patterns = [r'/item/(\d+)\.html', r'productIds=(\d+)', r'/(\d{10,})']
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                return match.group(1)
        return None
    except:
        return None

# Handlers مبسطة
@bot.message_handler(commands=['start'])
def welcome_user(message):
    bot.send_message(message.chat.id, 
        "مرحبا بكم👋\nأنا بوت AliExpress 🤖\nأرسل رابط المنتج وسأوفر لك عروض الخصم! 🔥",
        reply_markup=keyboardStart)

@bot.message_handler(func=lambda message: True)
def handle_links(message):
    try:
        if "aliexpress.com" not in message.text:
            bot.send_message(message.chat.id, "❌ يرجى إرسال رابط AliExpress صحيح")
            return
            
        wait_msg = bot.send_message(message.chat.id, '⏳ جاري المعالجة...')
        link = message.text
        
        product_id = extract_product_id(link)
        if not product_id:
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, "❌ لم أستطع استخراج معرف المنتج")
            return
        
        # إنشاء روابط مباشرة
        coin_link = f"https://m.aliexpress.com/p/coin-index/index.html?productIds={product_id}"
        encoded_url = quote_plus(link)
        bundle_link = f'https://star.aliexpress.com/share/share.htm?redirectUrl={encoded_url}?sourceType=560'
        super_link = f'https://star.aliexpress.com/share/share.htm?redirectUrl={encoded_url}?sourceType=562'
        limit_link = f'https://star.aliexpress.com/share/share.htm?redirectUrl={encoded_url}?sourceType=561'
        
        message_text = f"""
🛒 **تم المعالجة بنجاح!**
📦 المنتج: {product_id}

🎯 **العروض المتاحة:**

💰 عرض العملات:
{coin_link}

📦 عرض الحزمة:
{bundle_link}

💎 عرض السوبر:
{super_link}

🔥 عرض محدود:
{limit_link}
"""
        bot.delete_message(message.chat.id, wait_msg.message_id)
        bot.send_message(message.chat.id, message_text, reply_markup=keyboard)
        
    except Exception as e:
        bot.send_message(message.chat.id, "❌ حدث خطأ")

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_data().decode('UTF-8'))
        bot.process_new_updates([update])
        return 'OK', 200

if __name__ == "__main__":
    print("🚀 Starting bot...")
    webhook_url = os.getenv('RENDER_EXTERNAL_URL')
    if webhook_url:
        bot.remove_webhook()
        bot.set_webhook(url=f"{webhook_url}/webhook")
        print(f"✅ Webhook set to: {webhook_url}/webhook")
        app.run(host='0.0.0.0', port=5000)
    else:
        bot.infinity_polling()
