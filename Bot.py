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
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALIEXPRESS_API_PUBLIC = os.getenv('ALIEXPRESS_API_PUBLIC')
ALIEXPRESS_API_SECRET = os.getenv('ALIEXPRESS_API_SECRET')

if not TELEGRAM_BOT_TOKEN:
    print("X Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
print("✅ Telegram Bot initialized successfully")

# Keyboards
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

# دالة حل التوجيهات بشكل فعال
def resolve_redirects(link):
    """حل جميع توجيهات الرابط للحصول على الرابط النهائي"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        session = requests.Session()
        session.max_redirects = 10
        response = session.get(link, headers=headers, timeout=15, allow_redirects=True)
        
        final_url = response.url
        print(f"🔗 تم حل التوجيهات: {link} -> {final_url}")
        
        # إذا كان رابط star.aliexpress، استخرج redirectUrl
        if "star.aliexpress.com" in final_url:
            parsed_url = urlparse(final_url)
            params = parse_qs(parsed_url.query)
            if 'redirectUrl' in params:
                redirect_url = params['redirectUrl'][0]
                print(f"🔗 وجدت redirectUrl: {redirect_url}")
                if not redirect_url.startswith('http'):
                    redirect_url = 'https:' + redirect_url
                return resolve_redirects(redirect_url)
        
        return final_url
        
    except Exception as e:
        print(f"⚠️ خطأ في حل التوجيهات: {e}")
        return link

# دالة استخراج product_id محسنة
def extract_product_id(link):
    """استخراج معرف المنتج من جميع أنواع روابط AliExpress"""
    try:
        print(f"🔍 جاري استخراج product_id من: {link}")
        
        # حل التوجيهات أولاً
        resolved_link = resolve_redirects(link)
        print(f"🎯 الرابط بعد حل التوجيهات: {resolved_link}")
        
        # قائمة بأنماط الروابط المختلفة
        patterns = [
            # النمط الأساسي: /item/1005001234567890.html
            r'/item/(\d{8,})\.html',
            # نمط بدون .html: /item/1005001234567890
            r'/item/(\d{8,})(?:\?|$)',
            # نمط coin-index: productIds=1005001234567890
            r'[?&]productIds=(\d+)',
            # نمط تطبيق الجوال
            r'/(\d{8,})\?',
            # أي رقم طويل في الرابط
            r'/(\d{9,})',
            # نمط من query parameters
            r'[?&]id=(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, resolved_link)
            if match:
                product_id = match.group(1)
                print(f"✅ تم استخراج product_id باستخدام النمط '{pattern}': {product_id}")
                return product_id
        
        # إذا فشلت جميع الأنماط، جرب البحث عن أي رقم طويل
        numbers = re.findall(r'\d{8,}', resolved_link)
        if numbers:
            product_id = max(numbers, key=len)
            print(f"✅ تم استخراج product_id (أطول رقم): {product_id}")
            return product_id
        
        print(f"❌ لم أستطع استخراج product_id من الرابط: {resolved_link}")
        return None
        
    except Exception as e:
        print(f"❌ خطأ في استخراج product_id: {e}")
        return None

# دالة إنشاء روابط قصيرة باستخدام API
def generate_affiliate_links(product_id, original_link):
    """إنشاء روابط الخصم باستخدام AliExpress API"""
    try:
        # تنظيف الرابط الأصلي
        clean_link = original_link.split('?')[0]
        if not clean_link.endswith('.html'):
            clean_link += '.html'
            
        encoded_url = quote_plus(clean_link)
        
        # إنشاء روابط مباشرة (بدون API)
        direct_links = {
            'coin': f"https://m.aliexpress.com/p/coin-index/index.html?_immersiveMode=true&from=syicon&productIds={product_id}",
            'bundle': f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType=560',
            'super': f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType=562',
            'limit': f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType=561',
        }
        
        # إذا كان API متاحاً، حاول إنشاء روابط مختصرة
        if ALIEXPRESS_API_PUBLIC and ALIEXPRESS_API_SECRET:
            try:
                from aliexpress_api import AliexpressApi, models
                aliexpress = AliexpressApi(ALIEXPRESS_API_PUBLIC, ALIEXPRESS_API_SECRET,
                                         models.Language.AR, models.Currency.EUR, 'telegram_bot')
                
                # إنشاء روابط مختصرة باستخدام API
                coin_affiliate = aliexpress.get_affiliate_links(direct_links['coin'])
                if coin_affiliate and len(coin_affiliate) > 0:
                    direct_links['coin'] = coin_affiliate[0].promotion_link
                    
                bundle_affiliate = aliexpress.get_affiliate_links(direct_links['bundle'])
                if bundle_affiliate and len(bundle_affiliate) > 0:
                    direct_links['bundle'] = bundle_affiliate[0].promotion_link
                    
                super_affiliate = aliexpress.get_affiliate_links(direct_links['super'])
                if super_affiliate and len(super_affiliate) > 0:
                    direct_links['super'] = super_affiliate[0].promotion_link
                    
                limit_affiliate = aliexpress.get_affiliate_links(direct_links['limit'])
                if limit_affiliate and len(limit_affiliate) > 0:
                    direct_links['limit'] = limit_affiliate[0].promotion_link
                    
                print("✅ تم إنشاء روابط مختصرة باستخدام API")
                
            except Exception as api_error:
                print(f"⚠️ استخدام الروابط المباشرة بسبب خطأ API: {api_error}")
        
        return direct_links
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء الروابط: {e}")
        return None

# Handlers
@bot.message_handler(commands=['start'])
def welcome_user(message):
    bot.send_message(message.chat.id, 
        "مرحبا بكم👋\nأنا بوت AliExpress 🤖\nأرسل رابط المنتج وسأوفر لك عروض الخصم! 🔥",
        reply_markup=keyboardStart)

@bot.message_handler(func=lambda message: True)
def handle_links(message):
    try:
        # استخراج الرابط من الرسالة
        link_pattern = r'https?://[^\s]+'
        links = re.findall(link_pattern, message.text)
        
        if not links:
            bot.send_message(message.chat.id, "❌ يرجى إرسال رابط منتج AliExpress صحيح")
            return
            
        wait_msg = bot.send_message(message.chat.id, '⏳ جاري معالجة الرابط...')
        link = links[0]
        
        # التحقق من أن الرابط من AliExpress
        if "aliexpress.com" not in link and "alibaba.com" not in link:
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, "❌ يرجى إرسال رابط من AliExpress فقط")
            return
        
        product_id = extract_product_id(link)
        if not product_id:
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, "❌ لم أستطع استخراج معرف المنتج من الرابط\n\n🔍 **نصائح:**\n• تأكد أن الرابط يؤدي لصفحة منتج AliExpress\n• جرب نسخ الرابط مباشرة من المتصفح\n• تجنب الروابط القصيرة جداً")
            return
        
        # إنشاء روابط الخصم
        affiliate_links = generate_affiliate_links(product_id, link)
        
        if not affiliate_links:
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, "❌ حدث خطأ في إنشاء روابط الخصم")
            return
        
        message_text = f"""
🛒 **تم معالجة الرابط بنجاح!** ✅
📦 **معرف المنتج:** `{product_id}`

🎯 **عروض الخصم المتاحة:**

💰 **عرض العملات** (خصم فوري):
{affiliate_links['coin']}

📦 **عرض الحزمة** (خصومات متنوعة):
{affiliate_links['bundle']}

💎 **عرض السوبر** (خصومات إضافية):
{affiliate_links['super']}

🔥 **عرض محدود** (عروض خاصة):
{affiliate_links['limit']}

⚡️ **انقر على أي رابط لرؤية الخصم مباشرة!**
🔄 **جرب جميع الروابط لأفضل سعر!**
        """
        
        bot.delete_message(message.chat.id, wait_msg.message_id)
        bot.send_message(message.chat.id, message_text, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        print(f"❌ خطأ في handle_links: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ غير متوقع في المعالجة")

# Flask app
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
    print("🚀 Starting bot on Render...")
    webhook_url = os.getenv('RENDER_EXTERNAL_URL')
    
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
