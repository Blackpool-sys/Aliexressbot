import aiohttp
import asyncio
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AdvancedProductAPI:
    def __init__(self):
        self.sources = [
            {
                'name': 'flash_deals',
                'url': 'https://api.eprofit.com/v1/aliexpress/flash-deals',
                'priority': 10
            },
            {
                'name': 'hot_offers', 
                'url': 'https://ali.coupon.api/daily-hot-offers',
                'priority': 8
            }
        ]
    
    async def fetch_from_source(self, session, source):
        """جلب البيانات من مصدر محدد"""
        try:
            # محاكاة البيانات للاختبار (ستستبدل بـ APIs حقيقية)
            mock_offers = self.get_mock_offers(source['name'])
            return mock_offers
            
        except Exception as e:
            logger.error(f"Error fetching from {source['name']}: {str(e)}")
            return []
    
    def get_mock_offers(self, source_name):
        """بيانات تجريبية واقعية للعروض الساخنة"""
        mock_products = [
            {
                'title': 'Gaming Microphone USB RGB Condenser Mic',
                'original_price': 25.99,
                'current_price': 8.99,
                'sales': 284,
                'rating': 4.7,
                'product_url': 'https://aliexpress.com/item/gaming-mic',
                'time_left_hours': 6,
                'category': 'electronics'
            },
            {
                'title': 'Smart Watch Fitness Tracker Blood Oxygen',
                'original_price': 45.99,
                'current_price': 18.99,
                'sales': 1560,
                'rating': 4.5,
                'product_url': 'https://aliexpress.com/item/smart-watch',
                'time_left_hours': 12,
                'category': 'wearables'
            },
            {
                'title': 'Wireless Earbuds Bluetooth 5.3 Headphones',
                'original_price': 32.99,
                'current_price': 12.49,
                'sales': 892,
                'rating': 4.6,
                'product_url': 'https://aliexpress.com/item/wireless-earbuds',
                'time_left_hours': 18,
                'category': 'audio'
            },
            {
                'title': 'Portable Power Bank 10000mAh Fast Charging',
                'original_price': 28.99,
                'current_price': 9.99,
                'sales': 745,
                'rating': 4.4,
                'product_url': 'https://aliexpress.com/item/power-bank',
                'time_left_hours': 3,
                'category': 'electronics'
            },
            {
                'title': 'Mechanical Keyboard RGB Gaming Keyboard',
                'original_price': 52.99,
                'current_price': 22.99,
                'sales': 423,
                'rating': 4.8,
                'product_url': 'https://aliexpress.com/item/mechanical-keyboard',
                'time_left_hours': 24,
                'category': 'electronics'
            }
        ]
        
        processed_offers = []
        for product in mock_products:
            original_price = product['original_price']
            current_price = product['current_price']
            real_discount = ((original_price - current_price) / original_price) * 100
            
            if real_discount >= 30:
                product['real_discount'] = round(real_discount)
                product['source'] = source_name
                product['fetched_at'] = datetime.now().isoformat()
                processed_offers.append(product)
        
        return processed_offers
    
    async def get_real_discounts(self):
        """الجلب من جميع المصادر ودمج النتائج"""
        all_offers = []
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_from_source(session, source) for source in self.sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_offers.extend(result)
        
        return self.prioritize_offers(all_offers)
    
    def prioritize_offers(self, offers):
        """ترتيب العروض حسب الأفضلية"""
        scored_offers = []
        
        for offer in offers:
            score = 0
            
            # نقاط الخصم
            discount = offer.get('real_discount', 0)
            if discount > 70:
                score += 100
            elif discount > 50:
                score += 70
            elif discount > 30:
                score += 40
            
            # نقاط الوقت المحدود
            time_left = offer.get('time_left_hours', 999)
            if time_left < 6:
                score += 80
            elif time_left < 24:
                score += 50
            
            # نقاط المبيعات والشعبية
            sales = offer.get('sales', 0)
            if sales > 200:
                score += 30
            elif sales > 50:
                score += 15
            
            # نقاط التقييم
            rating = offer.get('rating', 0)
            if rating >= 4.5:
                score += 25
            elif rating >= 4.0:
                score += 15
            
            offer['hot_score'] = score
            scored_offers.append(offer)
        
        # الترتيب تنازلي وأخذ أفضل 30 عرض
        scored_offers.sort(key=lambda x: x['hot_score'], reverse=True)
        return scored_offers[:30]

# إنشاء كائن عالمي للاستخدام
advanced_api = AdvancedProductAPI()
