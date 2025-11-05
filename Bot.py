import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# التوكن من متغير البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found!")
    exit(1)

class BotFinder:
    def __init__(self):
        self.application = None
    
    def setup_bot(self):
        """إعداد البوت"""
        try:
            self.application = Application.builder().token(BOT_TOKEN).build()
            self._setup_handlers()
            logger.info("✅ BotFinder setup completed")
        except Exception as e:
            logger.error(f"❌ Bot setup failed: {e}")
            raise
    
    def _setup_handlers(self):
        """إعداد معالجات الأوامر"""
        handlers = [
            CommandHandler("start", self.start_command),
            CommandHandler("help", self.help_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message),
            CallbackQueryHandler(self.button_handler)
        ]
        
        for handler in handlers:
            self.application.add_handler(handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر البدء - نسخة طبق الأصل من BotFinder"""
        try:
            welcome_text = """🌐 **BotFinder Best Coupons**  
🤖 **بوت**  

---

- **مرحباً أنا BotFinder وهدفي مساعدتك في تقليل تكلفة المنتجات التي تبحث عنها.**  
  - من فضلك إقرار **دليل المستخدم** 👇

- **العروض تتطلب استخدام العملات:** يجب أن تعلم أن 100 عملة تعادل 1 دولار في تطبيق AliExpress لذا تأكد من أنه لديك ما يكفي.  
  - يجب أن يكون المنتج يدعم التخفيف بالعملات فإن لم يكن يدعمه فسأقوم بإعادة إرسال الرابط الذي أرسلته.  
  - في بعض الأحيان أرد عليك بنفس الرابط الذي أرسلته لأنه لا يوجد تخفيف أفضل من ذلك.  

- **روابط العرض المحدود:** في بعض الأحيان السعر مبالغ فيه هذا لأن العرض المحدود مخصص للمستخدمين الجدد.  
  - يمكنك أن تجرب الآن، أرسل لي رابط المنتج 📦

---

🎯 **للبدء، أرسل لي رابط منتج من AliExpress الآن!**"""

            # زر دليل المستخدم
            keyboard = [
                [InlineKeyboardButton("📖 دليل المستخدم", callback_data="user_guide")],
                [InlineKeyboardButton("🔄 كيف يعمل البوت", callback_data="how_it_works")],
                [InlineKeyboardButton("🎫 الحصول على عملات", callback_data="get_coins")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(welcome_text, reply_markup=reply_markup)
            logger.info(f"✅ User {update.effective_user.id} started BotFinder")
            
        except Exception as e:
            logger.error(f"❌ Start command error: {e}")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة ضغطات الأزرار"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "user_guide":
            await self.show_user_guide(query)
        elif data == "how_it_works":
            await self.show_how_it_works(query)
        elif data == "get_coins":
            await self.show_get_coins(query)
        elif data == "back_to_start":
            await self.back_to_start(query)
    
    async def show_user_guide(self, query):
        """دليل المستخدم"""
        guide_text = """📖 **دليل المستخدم BotFinder**

🎯 **كيفية الاستخدام:**
1. أرسل رابط منتج من AliExpress
2. سأبحث عن أفضل عرض بنفس المنتج
3. سأرسل لك الرابط مع الخصم

💰 **نظام العملات:**
- 100 عملة = 1 دولار
- العملات تستخدم للحصول على خصومات إضافية
- تأكد من امتلاكك عملات كافية

⚠️ **ملاحظات مهمة:**
- بعض المنتجات لا تدعم الخصم بالعملات
- قد أعيد نفس الرابط إذا لم أجد أفضل
- العروض المحدودة قد تكون أسعارها أعلى

🔄 **للبدء، أرسل رابط منتج الآن**"""

        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(guide_text, reply_markup=reply_markup)
    
    async def show_how_it_works(self, query):
        """كيف يعمل البوت"""
        how_it_works_text = """🔄 **كيف يعمل BotFinder؟**

1. **أرسل الرابط** 📤
   - أرسل لي أي رابط منتج من AliExpress

2. **البحث التلقائي** 🔍
   - سأبحث في قواعد البيانات عن نفس المنتج
   - سأبحث عن أفضل سعر متاح
   - سأتحقق من الخصومات والعروض

3. **الحصول على النتيجة** 🎯
   - سأرسل لك رابط بنفس المنتج
   - بسعر أفضل أو خصم إضافي
   - مع تفعيل نظام العملات إذا متاح

4. **التوفير** 💰
   - وفر حتى 80% من سعر المنتج
   - استفد من العروض الحصرية
   - احصل على شحن مجاني

🚀 **جرب الآن! أرسل رابط منتج**"""

        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(how_it_works_text, reply_markup=reply_markup)
    
    async def show_get_coins(self, query):
        """الحصول على عملات"""
        coins_text = """🎫 **كيفية الحصول على عملات AliExpress**

💰 **العملات:** 100 عملة = 1 دولار خصم

🔄 **طرق الحصول على العملات:**

1. **التسجيل اليومي** 📅
   - ادخل التطبيق يومياً
   - احصل على عملات مجانية

2. **إكمال المهام** ✅
   - شاهد منتجات
   - شارك في الألعاب
   - انهي المهام اليومية

3. **الشراء** 🛒
   - احصل على عملات مع كل شراء
   - كل دولار يعطيك عملات إضافية

4. **الدعوة** 👥
   - ادع أصدقاء للتطبيق
   - احصل على مكافآت عملات

📱 **لجمع العملات:**
1. افتح تطبيق AliExpress
2. اذهب إلى قسم "العملات"
3. ابدأ بجمع العملات المجانية

⚠️ **تأكد من وجود عملات كافية قبل طلب الخصم**"""

        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(coins_text, reply_markup=reply_markup)
    
    async def back_to_start(self, query):
        """العودة للبداية"""
        welcome_text = """🌐 **BotFinder Best Coupons**  
🤖 **بوت**  

---

- **مرحباً أنا BotFinder وهدفي مساعدتك في تقليل تكلفة المنتجات التي تبحث عنها.**  
  - من فضلك إقرار **دليل المستخدم** 👇

- **العروض تتطلب استخدام العملات:** يجب أن تعلم أن 100 عملة تعادل 1 دولار في تطبيق AliExpress لذا تأكد من أنه لديك ما يكفي.  
  - يجب أن يكون المنتج يدعم التخفيف بالعملات فإن لم يكن يدعمه فسأقوم بإعادة إرسال الرابط الذي أرسلته.  
  - في بعض الأحيان أرد عليك بنفس الرابط الذي أرسلته لأنه لا يوجد تخفيف أفضل من ذلك.  

- **روابط العرض المحدود:** في بعض الأحيان السعر مبالغ فيه هذا لأن العرض المحدود مخصص للمستخدمين الجدد.  
  - يمكنك أن تجرب الآن، أرسل لي رابط المنتج 📦

---

🎯 **للبدء، أرسل لي رابط منتج من AliExpress الآن!**"""

        keyboard = [
            [InlineKeyboardButton("📖 دليل المستخدم", callback_data="user_guide")],
            [InlineKeyboardButton("🔄 كيف يعمل البوت", callback_data="how_it_works")],
            [InlineKeyboardButton("🎫 الحصول على عملات", callback_data="get_coins")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(welcome_text, reply_markup=reply_markup)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل النصية - البحث عن عروض"""
        user_message = update.message.text
        user = update.effective_user
        
        # التحقق إذا كان الرابط من AliExpress
        if any(domain in user_message.lower() for domain in ['aliexpress', 'alibaba', 's.click.aliexpress']):
            await self.process_product_link(update, user_message)
        else:
            await self.ask_for_product_link(update)
    
    async def process_product_link(self, update: Update, product_link: str):
        """معالجة رابط المنتج - بنفس تنسيق الصورة"""
        try:
            # رسالة الانتظار
            processing_msg = await update.message.reply_text("🔍 **جاري البحث عن أفضل العروض...**\n\n⏳ قد يستغرق بضع ثوانٍ")
            
            # محاكاة البحث عن عروض (بنفس تنسيق الصورة)
            product_offers = self._generate_product_offers()
            
            # إرسال النتيجة بنفس تنسيق الصورة
            await processing_msg.edit_text("✅ **تم العثور على أفضل العروض!**")
            await self.send_product_offers(update, product_offers)
            
            logger.info(f"✅ Sent product offers to user {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"❌ Error processing product: {e}")
            await update.message.reply_text("❌ حدث خطأ أثناء المعالجة. يرجى المحاولة مرة أخرى.")
    
    def _generate_product_offers(self):
        """إنشاء عروض منتج بنفس تنسيق الصورة"""
        return {
            'product_name': 'Gaming Microphone USB Microphone for PC Condenser Podcast Mic for Studio Recording with Headphone Jack, Led, Noise Cancellation',
            'original_price': '$18.76',
            'offers': [
                {
                    'type': 'رابط الشراء بالعملات بـ',
                    'price': '$12.85',
                    'link': 's.click.aliexpress.com/e/_c45Dsear'
                },
                {
                    'type': 'المنتج في الـ',
                    'price': '$12.85',
                    'badge': 'BIG SAVE',
                    'link': 's.click.aliexpress.com/e/_c3MBg6dl'
                },
                {
                    'type': 'رابط بالعملات المحدود بـ',
                    'price': '$12.85', 
                    'link': 's.click.aliexpress.com/e/_c3LT4xvh'
                },
                {
                    'type': 'رابط الشراء في الـ',
                    'price': '$18.76',
                    'badge': 'Bundels',
                    'link': 's.click.aliexpress.com/e/_c3jGr1AF'
                },
                {
                    'type': 'المنتج في SuperDeals بـ',
                    'price': '$18.76',
                    'badge': 'StigerDeals',
                    'link': 's.click.aliexpress.com/e/_c3XTdly3'
                },
                {
                    'type': 'المنتج في العرض المحدود بـ',
                    'price': '$18.76', 
                    'badge': 'Clock',
                    'link': 'aliexpress.com/e/_c4c3fDNv'
                }
            ]
        }
    
    async def send_product_offers(self, update: Update, product_offers):
        """إرسال عروض المنتج بنفس تنسيق الصورة"""
        try:
            # جزء patents/certifications
            patents_text = """🌐 **BotFinder Best Coupons**  
🤖 **بوت**  

## patents/certifications

### إسم المنتج:
{product_name}

---

**سعر المنتج قبل استعمال البوت:**  
({original_price})  """.format(
                product_name=product_offers['product_name'],
                original_price=product_offers['original_price']
            )

            await update.message.reply_text(patents_text)

            # إرسال كل عرض على حدة بنفس التنسيق
            for offer in product_offers['offers']:
                offer_text = "- **{type}:**  \n".format(type=offer['type'])
                offer_text += "  ({price})".format(price=offer['price'])
                
                if 'badge' in offer:
                    offer_text += " ÷ {badge}".format(badge=offer['badge'])
                
                offer_text += "  \n  {link}".format(link=offer['link'])
                
                await update.message.reply_text(offer_text)

            # إرسال النصائح والإضافات
            tips_text = """---

**قم بتغيير الدولة مثلا لكندا**  
- بعدها ستلاحظ ارتفاع نسبة التخفيض بالعملات تصل لـ %55  

---

**يمكنني مساعدتك في تخفيض منتج آخر**  
23:59  

---

**عروض سماعات، ساعات، هواتف...**"""

            await update.message.reply_text(tips_text)

        except Exception as e:
            logger.error(f"❌ Error sending offers: {e}")
            await update.message.reply_text("❌ حدث خطأ في إرسال العروض.")
    
    async def ask_for_product_link(self, update: Update):
        """طلب رابط المنتج"""
        response_text = """📦 **أرسل رابط المنتج**

للبحث عن أفضل عرض، أرسل لي رابط منتج من AliExpress.

🌐 **مثال للرابط:**
`https://www.aliexpress.com/item/32956729189.html`
أو
`s.click.aliexpress.com/...`

🎯 **سأقوم بـ:**
- البحث عن أفضل العروض لنفس المنتج
- إرسال روابط بأسعار مخفضة
- تطبيق نظام العملات

🚀 **الآن، أرسل الرابط...**"""
        
        await update.message.reply_text(response_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر المساعدة"""
        help_text = """🆘 **مساعدة BotFinder**

🎯 **كيفية الاستخدام:**
1. أرسل /start للبداية
2. أرسل رابط منتج من AliExpress
3. احصل على أفضل العروض

📞 **للإبلاغ عن مشكلة:**
اتصل بالدعم الفني

🔄 **تذكر:**
- تأكد من وجود عملات كافية
- بعض المنتجات لا تدعم الخصم
- قد أعيد نفس الرابط إذا لم أجد أفضل"""
        
        await update.message.reply_text(help_text)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالج الأخطاء"""
        error = context.error
        logger.error(f"❌ Bot error: {error}")
    
    def run(self):
        """تشغيل البوت"""
        try:
            logger.info("🚀 Starting BotFinder...")
            self.application.run_polling()
        except Exception as e:
            logger.error(f"❌ Bot run failed: {e}")

def main():
    """الدالة الرئيسية"""
    try:
        logger.info("=" * 50)
        logger.info("🤖 BOTFINDER - STARTING...")
        logger.info("=" * 50)
        
        bot = BotFinder()
        bot.setup_bot()
        bot.run()
        
    except Exception as e:
        logger.error(f"❌ Bot crashed: {e}")

if __name__ == '__main__':
    main()
