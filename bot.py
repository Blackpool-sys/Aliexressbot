import re, os, asyncio, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# تحميل بيانات البيئة
load_dotenv()

# 🔧 استخدم التوكن مباشرة للتجربة - استبدل بالقيمة الحقيقية
TOKEN = "8587592919:AAFmqyGX3hC0xYSJ5QEihhrOrPegw7QaDBA"  # ❗ انسخ التوكن الحقيقي من BotFather

# إذا أردت استخدام Environment Variables، فعلق السطر above واستخدم هذا:
# TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 🧩 فك الرابط المختصر إن وجد
def expand_url(url: str):
    try:
        response = requests.get(url, allow_redirects=True, timeout=10)
        return response.url
    except Exception as e:
        print("❌ خطأ أثناء فك الرابط:", e)
        return url

# 🧩 استخراج product_id من الصفحة إذا فشل التحليل العادي
def extract_product_id_from_html(url: str):
    try:
        response = requests.get(url, timeout=10)
        html = response.text
        match = re.search(r'"productId":"(\d+)"', html)
        if match:
            return match.group(1)
    except Exception as e:
        print("⚠️ فشل استخراج productId من HTML:", e)
    return None

# 🧩 الأنماط العادية لاستخراج المعرف
def extract_product_id(url: str):
    patterns = [
        r"item/(\d+)\.html",
        r"product/(\d+)\.html",
        r"offer/(\d+)\.html",
        r"productId=(\d+)",
        r"/(\d+)\.html"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# 🧩 دالة محاكاة لجلب بيانات المنتج (بدون API)
def get_product_details(product_id: str):
    print(f"🔍 جلب بيانات المنتج: {product_id}")
    
    # بيانات منتج تجريبي
    return {
        "aliexpress_affiliate_productdetail_get_response": {
            "resp_result": {
                "result": {
                    "products": [{
                        "product_title": f"منتج تجريبي - {product_id}",
                        "product_main_image_url": "https://via.placeholder.com/300/0088cc/FFFFFF?text=Product+Image",
                        "target_sale_price": "29.99",
                        "store_info": {
                            "store_name": "متجر تجريبي", 
                            "store_rating": "4.8"
                        },
                        "logistics_info": [{
                            "logistics_company": "محرز اكسبريس"
                        }],
                        "commission_rate": "6.0",
                        "promotion_link": f"https://aliexpress.com/item/{product_id}.html"
                    }]
                }
            }
        }
    }

# 🧩 دالة تحويل العملة
def usd_to_dzd(usd_price: float) -> float:
    """تحويل الدولار إلى الدينار الجزائري"""
    try:
        response = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=DZD", timeout=10)
        rate = response.json()["rates"]["DZD"]
        return round(usd_price * rate, 2)
    except Exception:
        # سعر افتراضي إذا فشل API
        return usd_price * 135

# 🎯 التعامل مع الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not any(domain in text for domain in ["aliexpress.com", "click.aliexpress.com"]):
        await update.message.reply_text("🔗 أرسل رابط منتج من AliExpress.")
        return

    await update.message.reply_text("🔄 جاري فك الرابط المختصر...")
    
    try:
        url = expand_url(text)
        await update.message.reply_text(f"🔗 الرابط بعد الفك:\n{url}")
        
        # محاولة استخراج ID
        product_id = extract_product_id(url)
        if not product_id:
            await update.message.reply_text("🔄 جاري البحث عن معرف المنتج في الصفحة...")
            product_id = extract_product_id_from_html(url)

        if not product_id:
            await update.message.reply_text("⚠️ لم أستطع تحديد معرف المنتج من الرابط.")
            return

        await update.message.reply_text(f"✅ تم العثور على معرف المنتج: {product_id}")
        await update.message.reply_text("⌛ جاري جلب تفاصيل المنتج...")

        data = get_product_details(product_id)
        
        if not data:
            raise Exception("لا توجد بيانات مستلمة")

        resp = data.get("aliexpress_affiliate_productdetail_get_response", {})
        result = resp.get("resp_result", {}).get("result", {})

        if not result or "products" not in result:
            raise Exception("لم يتم العثور على بيانات المنتج في الرد.")

        product = result["products"][0]

        # استخراج البيانات
        title = product.get("product_title", "بدون عنوان")
        image = product.get("product_main_image_url")
        usd_price = float(product.get("target_sale_price", 0))
        dzd_price = usd_to_dzd(usd_price)
        store = product.get("store_info", {}).get("store_name", "غير معروف")
        rating = product.get("store_info", {}).get("store_rating", "0.0")
        
        # التعامل مع shipping بشكل آمن
        logistics_info = product.get("logistics_info", [{}])
        shipping = logistics_info[0].get("logistics_company", "غير محدد") if logistics_info else "غير محدد"
        
        commission = product.get("commission_rate", "0.0")
        link = product.get("promotion_link", url)

        # تنسيق الرسالة
        message = (
            f"*🎯 {title}*\n\n"
            f"💲 *السعر:* ${usd_price:.2f}\n"
            f"🇩🇿 *السعر بالدينار:* {dzd_price:,.0f} DA\n\n"
            f"🏪 *المتجر:* {store}\n"
            f"⭐ *التقييم:* {rating}\n"
            f"🚚 *الشحن:* {shipping}\n"
            f"💰 *العمولة:* {commission}%\n\n"
            f"🔗 [رابط المنتج]({link})"
        )

        # إرسال الصورة إذا كانت متاحة
        if image and image.startswith('http'):
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image,
                caption=message,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        print("❌ خطأ أثناء معالجة المنتج:", e)
        error_msg = f"⚠️ حدث خطأ أثناء جلب البيانات.\n\nخطأ: {str(e)}"
        await update.message.reply_text(error_msg)

# ✅ بدء البوت
def main():
    try:
        print(f"🔑 جاري تشغيل البوت بالتوكن: {TOKEN[:10]}...")  # طباعة جزء من التوكن للتأكد
        
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("🤖 البوت يعمل الآن...")
        app.run_polling()
        
    except Exception as e:
        print(f"❌ فشل تشغيل البوت: {e}")

if __name__ == "__main__":
    main()
