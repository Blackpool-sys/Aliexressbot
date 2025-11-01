import os
import logging

class Config:
    """إعدادات التطبيق من متغيرات البيئة"""
    
    def __init__(self):
        # إعدادات البوت الأساسية (مطلوبة)
        self.BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
        self.AFFILIATE_TAG = os.environ.get('AFFILIATE_TAG', '')
        
        # إعدادات API إضافية (اختيارية)
        self.ALIEXPRESS_APP_KEY = os.environ.get('ALIEXPRESS_APP_KEY', '')
        self.ALIEXPRESS_APP_SECRET = os.environ.get('ALIEXPRESS_APP_SECRET', '')
        
        # إعدادات التطبيق
        self.DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
        
        self.validate_config()
    
    def validate_config(self):
        """التحقق من صحة الإعدادات المطلوبة"""
        missing_vars = []
        
        if not self.BOT_TOKEN:
            missing_vars.append('BOT_TOKEN')
        
        if not self.AFFILIATE_TAG:
            missing_vars.append('AFFILIATE_TAG')
        
        if missing_vars:
            error_msg = f"❌ المتغيرات البيئية المطلوبة غير معينة: {', '.join(missing_vars)}\n"
            error_msg += "📝 يرجى تعيينها في Render Dashboard → Environment Variables"
            raise ValueError(error_msg)
        
        logging.info("✅ تم تحميل الإعدادات بنجاح من متغيرات البيئة")
        logging.info(f"🤖 البوت جاهز - التاغ التابع: {self.AFFILIATE_TAG}")
    
    def __str__(self):
        """عرض الإعدادات (بدون معلومات حساسة)"""
        return (f"Config(BOT_TOKEN={'***' if self.BOT_TOKEN else 'Missing'}, "
                f"AFFILIATE_TAG={self.AFFILIATE_TAG}, "
                f"DEBUG={self.DEBUG})")
