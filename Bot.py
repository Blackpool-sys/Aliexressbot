import re, os, asyncio, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# تحميل بيانات البيئة
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# دالة فك الرابط المختصر
def expand_url(url: str):
    try:
        response = requests.get(url, allow_redirects=True, timeout=15)
        return response.url
    except Exception as e:
        print("❌ خطأ أثناء فك الرابط:", e)
        return url

# استخراج product_id
def extract_product_id(url: str):
    patterns = [
        r"item/(\d+)\.html",
        r"product/(\d+)\.html", 
        r"/(\d+)\.html"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# دالة جلب تفاصيل المنتج (مؤقتة - تحتاج API حقيقي)
def get_product_details(product_id):
    # هذه دالة مؤقتة - تحتاج استبدالها بـ API حقيقي
    return {
        "aliexpress_affiliate_productdetail_get_response": {
            "resp_result": {
                "result": {
                    "products": [{
                        "product_title": "منتج تجريبي",
                        "product_main_image_url": "https://via.placeholder.com/300",
                        "target_sale_price": "25.99",
                        "store_info": {"store_name": "متجر تجريبي", "store_rating": "4.5"},
                        "logistics_info": [{"logistics_company": "محرز اكسبريس"}],
                        "commission_rate": "5.0",
                        "promotion_link": f"https://aliexpress.com/item/{product_id}.html"
                    }]
                }
            }
        }
    }

# دالة تحويل العملة
def usd_to_dzd(usd_price):
    return usd_price * 135  # سعر تحويل تقريبي

# التعامل مع الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not any(domain in text for domain in ["aliexpress.com", "click.aliexpress.com"]):
        await update.message.reply_text("🔗 أرسل رابط منتج من AliExpress.")
        return

    await update.message.reply_text("🔄 جاري فك الرابط...")
    
    try:
        url = expand_url(text)
        product_id = extract_product_id(url)
        
        if not product_id:
            await update.message.reply_text("⚠️ لم أستطع تحديد معرف المنتج.")
            return

        await update.message.reply_text("⌛ جاري جلب تفاصيل المنتج...")
        data = get_product_details(product_id)
        
        product = data["aliexpress_affiliate_productdetail_get_response"]["resp_result"]["result"]["products"][0]
        title = product.get("product_title", "بدون عنوان")
        image = product.get("product_main_image_url")
        usd_price = float(product.get("target_sale_price", 0))
        dzd_price = usd_to_dzd(usd_price)
        store = product.get("store_info", {}).get("store_name", "غير معروف")
        rating = product.get("store_info", {}).get("store_rating", "0.0")
        shipping = product.get("logistics_info", [{}])[0].get("logistics_company", "غير محدد")
        commission = product.get("commission_rate", "0.0")
        link = product.get("promotion_link", url)

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

        if image:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image,
                caption=message,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ: {str(e)}")

# بدء البوت
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 البوت يعمل الآن على Render...")
    app.run_polling()

if __name__ == "__main__":
    main()
