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

# دالة استخراج product_id محسنة تعمل مع جميع الروابط
def extract_product_id(link):
    """استخراج معرف المنتج من جميع أنواع روابط AliExpress"""
    try:
        print(f"🔍 جاري استخراج product_id من: {link}")
        
        # تنظيف الرابط وإزالة المسافات
        link = link.strip()
        
        # قائمة بأنماط الروابط المختلفة
        patterns = [
            # النمط الأساسي: /item/1005001234567890.html
            r'/item/(\d+)\.html',
            # نمط بدون .html: /item/1005001234567890
            r'/item/(\d+)(?:\?|$)',
            # نمط coin-index: productIds=1005001234567890
            r'[?&]productIds=(\d+)',
            # نمط تطبيق الجوال
            r'/(\d+)\?',
            # نمط من query parameters
            r'[?&]id=(\d+)',
            # نمط الروابط القصيرة
            r'/(\d{8,})',
            # أي رقم طويل في الرابط (الطريقة العامة)
            r'(\d{8,})',
        ]
        
        # جرب كل نمط على الرابط مباشرة بدون حل التوجيهات أولاً
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                product_id = match.group(1)
                print(f"✅ تم استخراج product_id: {product_id}")
                return product_id
        
        print(f"❌ لم أستطع استخراج product_id من الرابط")
        return None
        
    except Exception as e:
        print(f"❌ خطأ في استخراج product_id: {e}")
        return None

# دالة إنشاء روابط مختصرة باستخدام AliExpress API
def generate_short_links(product_id, original_link):
    """إنشاء روابط مختصرة باستخدام AliExpress API"""
    try:
        # تنظيف الرابط الأصلي
        clean_link = original_link.split('?')[0]
        if not clean_link.endswith('.html'):
            clean_link += '.html'
            
        encoded_url = quote_plus(clean_link)
        
        # الروابط الأساسية
        base_links = {
            'coin': f"https://m.aliexpress.com/p/coin-index/index.html?_immersiveMode=true&from=syicon&productIds={product_id}",
            'bundle': f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType=560',
            'super': f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType=562',
            'limit': f'https://star.aliexpress.com/share/share.htm?platform=AE&businessType=ProductDetail&redirectUrl={encoded_url}?sourceType=561',
        }
        
        # إذا كانت مفاتيح API متاحة، حاول إنشاء روابط مختصرة
        short_links = base_links.copy()
        
        if ALIEXPRESS_API_PUBLIC and ALIEXPRESS_API_SECRET:
            try:
                from aliexpress_api import AliexpressApi, models
                aliexpress = AliexpressApi(ALIEXPRESS_API_PUBLIC, ALIEXPRESS_API_SECRET,
                                         models.Language.AR, models.Currency.EUR, 'telegram_bot')
                print("✅ استخدام API لإنشاء روابط مختصرة")
                
                # إنشاء روابط مختصرة لكل نوع
                for link_type, url in base_links.items():
                    try:
                        affiliate_links = aliexpress.get_affiliate_links(url)
                        if affiliate_links and len(affiliate_links) > 0:
                            short_links[link_type] = affiliate_links[0].promotion_link
                            print(f"✅ تم اختصار رابط {link_type}")
                        else:
                            print(f"⚠️ لم يتم اختصار رابط {link_type}، استخدام الرابط الأساسي")
                    except Exception as e:
                        print(f"⚠️ خطأ في اختصار رابط {link_type}: {e}")
                        short_links[link_type] = url
                        
            except Exception as api_error:
                print(f"⚠️ استخدام الروابط الأساسية بسبب خطأ API: {api_error}")
                short_links = base_links
        else:
            print("ℹ️ استخدام الروابط الأساسية (لا توجد مفاتيح API)")
            short_links = base_links
        
        return short_links
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء الروابط: {e}")
        # في حالة الخطأ، ارجع للروابط الأساسية
        return {
            'coin': f"https://m.aliexpress.com/p/coin-index/index.html?productIds={product_id}",
            'bundle': f'https://star.aliexpress.com/share/share.htm?redirectUrl={quote_plus(original_link)}?sourceType=560',
            'super': f'https://star.aliexpress.com/share/share.htm?redirectUrl={quote_plus(original_link)}?sourceType=562',
            'limit': f'https://star.aliexpress.com/share/share.htm?redirectUrl={quote_plus(original_link)}?sourceType=561',
        }

# دالة الحصول على معلومات المنتج
def get_product_info(product_id):
    """الحصول على معلومات المنتج (العنوان، السعر، الصورة)"""
    try:
        if ALIEXPRESS_API_PUBLIC and ALIEXPRESS_API_SECRET:
            from aliexpress_api import AliexpressApi, models
            aliexpress = AliexpressApi(ALIEXPRESS_API_PUBLIC, ALIEXPRESS_API_SECRET,
                                     models.Language.AR, models.Currency.EUR, 'telegram_bot')
            
            product_details = aliexpress.get_products_details(
                [product_id], 
                fields=["target_sale_price", "product_title", "product_main_image_url"]
            )
            
            if product_details and len(product_details) > 0:
                price = float(product_details[0].target_sale_price)
                title = product_details[0].product_title
                image = product_details[0].product_main_image_url
                
                # تحويل السعر إلى الدرهم المغربي
                try:
                    response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
                    data = response.json()
                    exchange_rate = data['rates']['MAD']
                    price_mad = price * exchange_rate
                except:
                    price_mad = price * 10  # سعر افتراضي
                
                return {
                    'title': title,
                    'price_usd': price,
                    'price_mad': price_mad,
                    'image': image,
                    'success': True
                }
        
        # إذا فشل الحصول على المعلومات من API
        return {
            'title': f"منتج AliExpress - {product_id}",
            'price_usd': 0.0,
            'price_mad': 0.0,
            'image': "https://via.placeholder.com/300x300?text=AliExpress+Product",
            'success': False
        }
        
    except Exception as e:
        print(f"⚠️ لم أستطع الحصول على معلومات المنتج: {e}")
        return {
            'title': f"منتج AliExpress - {product_id}",
            'price_usd': 0.0,
            'price_mad': 0.0,
            'image': "https://via.placeholder.com/300x300?text=AliExpress+Product",
            'success': False
        }

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
        if "aliexpress.com" not in link.lower():
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, "❌ يرجى إرسال رابط من AliExpress فقط")
            return
        
        product_id = extract_product_id(link)
        if not product_id:
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, 
                "❌ لم أستطع استخراج معرف المنتج من الرابط\n\n"
                "🔍 **نصائح:**\n"
                "• تأكد أن الرابط يؤدي لصفحة منتج AliExpress\n"
                "• جرب نسخ الرابط مباشرة من المتصفح\n"
                "• تجنب الروابط التي تحتوي على نص إضافي")
            return
        
        # الحصول على معلومات المنتج
        product_info = get_product_info(product_id)
        
        # إنشاء روابط الخصم المختصرة
        affiliate_links = generate_short_links(product_id, link)
        
        if not affiliate_links:
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, "❌ حدث خطأ في إنشاء روابط الخصم")
            return
        
        # بناء الرسالة
        if product_info['success']:
            message_text = f"""
🛒 **{product_info['title']}**
💰 السعر: ${product_info['price_usd']:.2f} | {product_info['price_mad']:.2f} درهم

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
            """
        else:
            message_text = f"""
🛒 **منتج AliExpress** - {product_id}

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
            """
        
        bot.delete_message(message.chat.id, wait_msg.message_id)
        
        # إرسال الصورة مع التفاصيل
        bot.send_photo(
            message.chat.id,
            product_info['image'],
            caption=message_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
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
