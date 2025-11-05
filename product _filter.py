import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartProductFilter:
    def __init__(self):
        self.min_discount = 30  # أقل خصم مقبول
        self.min_rating = 4.0   # أقل تقييم مقبول
        self.min_sales = 10     # أقل مبيعات مقبولة
    
    def filter_hot_products(self, products):
        """تصفية المنتجات الساخنة فقط"""
        filtered_products = []
        
        for product in products:
            try:
                # التحقق من الشروط الأساسية
                if (product.get('real_discount', 0) >= self.min_discount and
                    product.get('rating', 0) >= self.min_rating and
                    product.get('sales', 0) >= self.min_sales):
                    
                    # إضافة معلومات إضافية للعرض
                    product = self.enhance_product_data(product)
                    filtered_products.append(product)
                    
            except Exception as e:
                logger.error(f"Error filtering product: {str(e)}")
                continue
        
        return filtered_products
    
    def enhance_product_data(self, product):
        """تحسين بيانات المنتج للإظهار"""
        discount = product.get('real_discount', 0)
        
        # تحديد نوع العرض
        if discount > 70:
            product['offer_type'] = 'عرض رائع 🔥'
            product['emoji'] = '🔥🔥'
        elif discount > 50:
            product['offer_type'] = 'عرض ممتاز ⚡'  
            product['emoji'] = '⚡'
        else:
            product['offer_type'] = 'عرض جيد ✅'
            product['emoji'] = '✅'
        
        # تنسيق الوقت المتبقي
        time_left = product.get('time_left_hours', 24)
        if time_left < 6:
            product['time_text'] = f'ينتهي قريباً ⏰ ({time_left} ساعة)'
        elif time_left < 24:
            product['time_text'] = f'ينتهي اليوم 🕒 ({time_left} ساعة)'
        else:
            product['time_text'] = f'صالح ({time_left} ساعة)'
        
        return product
    
    def get_top_offers_by_category(self, products, category=None, limit=10):
        """الحصول على أفضل العروض حسب التصنيف"""
        filtered = self.filter_hot_products(products)
        
        if category:
            filtered = [p for p in filtered if p.get('category') == category]
        
        # ترتيب حسب النقاط
        filtered.sort(key=lambda x: x.get('hot_score', 0), reverse=True)
        return filtered[:limit]

# كائن عالمي للاستخدام
product_filter = SmartProductFilter()
