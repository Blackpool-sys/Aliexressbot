import os
import logging
import re
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from config import Config
from aliexpress_api import AliExpressAPI

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AliExpressAffiliateBot:
    def __init__(self):
        # تحميل الإعدادات من متغيرات البيئة مباشرة
        try:
            self.config = Config()
            self.api = AliExpressAPI(self.config)
            
            self.updater = Updater(token=self.config.BOT_TOKEN, use_context=True)
            self.dispatcher = self.updater.dispatcher
            
            self.setup_handlers()
            logger.info("✅ تم تهيئة البوت بنجاح")
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة البوت: {e}")
            raise
    
    def setup_handlers(self):
        """إعداد معالجات الأوامر والرسائل"""
        self.dispatcher.add_handler(CommandHandler("start", self.start_command))
        self.dispatcher.add_handler(CommandHandler("help", self.help_command))
        self.dispatcher.add_handler(CommandHandler("info", self.info_command))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        
        self.dispatcher.add_error_handler(self.error_handler)
    
    def start_command(self, update: Update, context: CallbackContext):
        """رد على أمر /start"""
        user = update.effective_user
        welcome_text = f"""
🎯 **مرحباً {user.first_name}!**

أنا بوت التسويق بالعمولة لـ AliExpress 🤖

📌 **كيفية الاستخدام:**
1. اذهب إلى AliExpress
2. اختر المنتج المطلوب  
3. انسخ الرابط
4. أرسله لي

وسأزودك بروابط العمولة مع أفضل العروض!

🔹 /help - للمساعدة
🔹 /info - معلومات البوت
        """
        update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    def help_command(self, update: Update, context: CallbackContext):
        """رد على أمر /help"""
        help_text = """
🆘 **مساعدة:**

- أرسل رابط منتج من AliExpress
- سأرد عليك بروابط العمولة المختلفة
- يمكنك استخدام الروابط للتسويق والربح

📎 **مثال للرابط:** 
`https://www.aliexpress.com/item/1234567890.html`

🔧 **الأوامر المتاحة:**
/start - بدء الاستخدام
/help - عرض هذه المساعدة  
/info - معلومات البوت

💡 **نصائح:**
- تأكد من صحة الرابط
- الروابط تعمل لمدة 30 يوم
- يمكنك تتبع الأرباح من لوحة التحكم
        """
        update.message.reply_text(help_text, parse_mode='Markdown')
    
    def info_command(self, update: Update, context: CallbackContext):
        """معلومات عن البوت"""
        info_text = f"""
🤖 **معلومات البوت:**

✅ البوت يعمل بشكل طبيعي
🆔 التاغ التابع: `{self.config.AFFILIATE_TAG}`
🔧 الإصدار: 2.0
🐍 Python: 3.9
📊 الخدمة: Render.com (Worker)

📨 أرسل رابط منتج للبدء!
        """
        update.message.reply_text(info_text, parse_mode='Markdown')
    
    def extract_product_info(self, url):
        """استخراج معلومات المنتج من الرابط"""
        try:
            logger.info(f"جاري استخراج معلومات المنتج من: {url[:100]}...")
            
            # تنظيف الرابط
            clean_url = url.split('?')[0].strip()
            
            # أنماط مختلفة لروابط AliExpress
            patterns = [
                r'/item/(\d+?)\.html',
                r'/item/(\d+)',
                r'/(\d+)\.html',
                r'_(\d+)\.html'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, clean_url)
                if match:
                    product_id = match.group(1)
                    logger.info(f"تم العثور على رقم المنتج: {product_id}")
                    return product_id
            
            logger.warning(f"لم يتم العثور على رقم منتج في الرابط: {clean_url}")
            return None
            
        except Exception as e:
            logger.error(f"خطأ في استخراج معلومات المنتج: {e}")
            return None
    
    def handle_message(self, update: Update, context: CallbackContext):
        """معالجة الرسائل الواردة"""
        user_message = update.message.text.strip()
        user_id = update.effective_user.id
        
        logger.info(f"رسالة مستلم من المستخدم {user_id}: {user_message[:50]}...")
        
        # التحقق إذا كان الرابط من AliExpress
        if any(domain in user_message.lower() for domain in ['aliexpress.com', 'alixpress.com']):
            try:
                update.message.reply_chat_action('typing')
                
                # استخراج معلومات المنتج
                product_id = self.extract_product_info(user_message)
                
                if not product_id:
                    update.message.reply_text(
                        "❌ **لم أستطع التعرف على المنتج من الرابط**\n\n"
                        "تأكد من أن الرابط صالح ويحتوي على رقم المنتج.\n"
                        "مثال: `https://www.aliexpress.com/item/4001234567890.html`",
                        parse_mode='Markdown'
                    )
                    return
                
                # إنشاء روابط العمولة
                logger.info(f"جاري إنشاء روابط العمولة للمنتج: {product_id}")
                links_data = self.api.generate_affiliate_links(product_id)
                
                if links_data and 'links' in links_data:
                    response_message = self.create_response_message(links_data)
                    update.message.reply_text(
                        response_message, 
                        parse_mode='Markdown', 
                        disable_web_page_preview=True
                    )
                    
                    logger.info(f"تم إنشاء الروابط بنجاح للمنتج {product_id} للمستخدم {user_id}")
                    
                else:
                    error_msg = (
                        "❌ **عذراً، لم أستطع إنشاء روابط العمولة**\n\n"
                        "قد يكون بسبب:\n"
                        "• المنتج غير متوفر\n"
                        "• مشكلة في الخدمة\n"
                        "• الرابط غير صالح"
                    )
                    update.message.reply_text(error_msg)
                    logger.error(f"فشل في إنشاء روابط للمنتج {product_id}")
                    
            except Exception as e:
                logger.error(f"خطأ في معالجة الرسالة: {e}")
                update.message.reply_text("❌ **حدث خطأ غير متوقع**\n\nيرجى المحاولة مرة أخرى لاحقاً.")
                
        else:
            update.message.reply_text(
                "📨 **يرجى إرسال رابط منتج من AliExpress فقط**\n\n"
                "مثال:\n"
                "`https://www.aliexpress.com/item/4001234567890.html`",
                parse_mode='Markdown'
            )
    
    def create_response_message(self, links_data):
        """إنشاء رسالة الرد بالتنسيق المطلوب"""
        product_title = links_data.get('title', 'منتج AliExpress')
        links = links_data['links']
        
        # تقصير العنوان إذا كان طويلاً
        if len(product_title) > 60:
            display_title = product_title[:60] + "..."
        else:
            display_title = product_title
        
        message = f"🎯 **تخفيض ل {display_title}**\n\n"
        
        message += "✅ **بما أنه هناك مشاكل في تخفيض العملات هذا رابط بديل للمنتج في صفحة العملات وستجد أفضل سعر** 👇\n"
        message += f"🌐 {links['main']}\n\n"
        
        message += "🪙 **سعر التخفيض بالعملات**\n\n"
        message += f"🔗 {links['coins']}\n\n"
        
        message += "🛒 **سعر السوبر ديلز**\n\n"
        message += f"🔗 {links['super_deals']}\n\n"
        
        message += "🏅 **سعر العرض المحدود**\n\n"
        message += f"🔗 {links['limited_offer']}\n\n"
        
        message += "📌 **رابط الـ bundle deals**\n\n"
        message += f"🔗 {links['bundle_deals']}\n\n"
        
        message += "---\n"
        message += "💡 **ملاحظة:** جميع الروابط تحتوي على عمولتك الخاصة\n"
        message += f"🆔 **رقم المنتج:** `{links_data.get('product_id', 'N/A')}`\n"
        message += "⏰ **الروابط صالحة لمدة 30 يوم**"
        
        return message
    
    def error_handler(self, update: Update, context: CallbackContext):
        """معالجة الأخطاء"""
        logger.error(f"حدث خطأ: {context.error}")
        
        if update and update.effective_message:
            try:
                update.effective_message.reply_text(
                    "❌ **حدث خطأ غير متوقع**\n\nيرجى المحاولة مرة أخرى لاحقاً."
                )
            except Exception as e:
                logger.error(f"فشل في إرسال رسالة الخطأ: {e}")
    
    def start(self):
        """بدء تشغيل البوت"""
        logger.info("🎉 بدء تشغيل بوت عمولة AliExpress...")
        
        # بدء البوت
        self.updater.start_polling(
            drop_pending_updates=True,
            timeout=30,
            read_latency=5.0
        )
        
        logger.info("✅ البوت يعمل وجاهز لاستقبال الرسائل!")
        
        # الحفاظ على البوت شغال
        self.updater.idle()

def main():
    """الدالة الرئيسية"""
    try:
        # التحقق من وجود المتغيرات الأساسية قبل البدء
        required_vars = ['BOT_TOKEN', 'AFFILIATE_TAG']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            print(f"❌ ERROR: Missing environment variables: {', '.join(missing_vars)}")
            print("📝 Please set them in Render Dashboard → Environment Variables")
            return
        
        print("🚀 Starting AliExpress Affiliate Bot...")
        print("📝 Service Type: Background Worker")
        print("🔧 Initializing bot...")
        
        bot = AliExpressAffiliateBot()
        
        print("✅ Bot initialized successfully!")
        print("🤖 Bot is now running and ready to receive messages...")
        
        bot.start()
        
    except Exception as e:
        logger.error(f"❌ فشل في تشغيل البوت: {e}")
        print(f"❌ فشل في تشغيل البوت: {e}")

if __name__ == '__main__':
    main()
