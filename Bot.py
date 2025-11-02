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

# دالة استخراج product_id محسنة
def extract_product_id(link):
    """استخراج معرف المنتج من جميع أنواع روابط AliExpress"""
    try:
        print(f"🔍 جاري استخراج product_id من: {link}")
        
        # أولاً: حل أي توجيهات في الرابط
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(link, headers=headers, timeout=10, allow_redirects=True)
            final_url = response.url
            print(f"🔗 الرابط النهائي: {final_url}")
        except:
            final_url = link
        
        # قائمة بأنماط الروابط المختلفة
        patterns = [
            r'/item/(\d{8,})\.html',
            r'/item/(\d{8,})(?:\?|$)',
            r'[?&]productIds=(\d+)',
            r'/(\d{8,})\?',
            r'/(\d{10,})',
            r'[?&]id=(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, final_url)
            if match:
                product_id = match.group(1)
                print(f"✅ تم استخراج product_id: {product_id}")
                return product_id
        
        numbers = re.findall(r'\d{8,}', final_url)
        if numbers:
            product_id = max(numbers, key=len)
            print(f"✅ تم استخراج product_id (أطول رقم): {product_id}")
            return product_id
        
        print(f"❌ لم أستطع استخراج product_id من الرابط")
        return None
        
    except Exception as e:
        print(f"❌ خطأ في استخراج product_id: {e}")
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
        
        if not links or "aliexpress.com" not in message.text.lower():
            bot.send_message(message.chat.id, "❌ يرجى إرسال رابط منتج AliExpress صحيح")
            return
            
        wait_msg = bot.send_message(message.chat.id, '⏳ جاري معالجة الرابط...')
        link = links[0]
        
        product_id = extract_product_id(link)
        if not product_id:
            bot.delete_message(message.chat.id, wait_msg.message_id)
            bot.send_message(message.chat.id, "❌ لم أستطع استخراج معرف المنتج من الرابط\n⚠️ تأكد أن الرابط يؤدي لصفحة منتج AliExpress")
            return
        
        # إنشاء روابط الخصم
        coin_link = f"https://m.al
