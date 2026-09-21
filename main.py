import os
import threading
import requests
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Yapılandırma Bilgileri
TOKEN = "8966819189:AAFhWDClW5LfI1UQeKZqhgu8C8OCR-qjqzY"
API_KEY = "sms_78764ab234637198f606b1bb0ce55ced58aabbb2f1be18b3"
TARGET_NAME = "Resul Sakal"
IBAN = "TR62 0006 2000 5000 0006 8107 73"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_countries = {}

@app.route('/')
def home():
    return "ANGA VIP SERVICES Bot Aktif ve Calisiyor!"

# Render'ın port isteğini karşılamak için mini web sunucusu
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🇹🇷 Türkiye - WhatsApp", callback_data="country_0"))
    markup.add(InlineKeyboardButton("🇺🇸 Amerika - WhatsApp", callback_data="country_12"))
    markup.add(InlineKeyboardButton("🇬🇧 İngiltere - WhatsApp", callback_data="country_16"))
    
    bot.send_message(
        message.chat.id, 
        "ANGA VIP SERVICES Bot aktif!\n\nLütfen almak istediğiniz ülkeyi seçin:", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    bot.answer_callback_query(call.id)
    
    if data.startswith("country_"):
        country_id = data.split("_")[1]
        user_countries[call.message.chat.id] = country_id
        
        country_names = {"0": "Türkiye", "12": "Amerika", "16": "İngiltere"}
        c_name = country_names.get(country_id, "Türkiye")
        
        bot.send_message(
            call.message.chat.id, 
            f"Seçilen Ürün: 🇹🇷 {c_name} - WhatsApp\nTutar: 150 TL\n\n"
            f"📌 Ödeme Bildirimi:\n"
            f"Alıcı: {TARGET_NAME}\n"
            f"IBAN: {IBAN}\n\n"
            f"Lütfen yukarıdaki IBAN'a ödemeyi yaptıktan sonra dekontu (fotoğraf veya dosya olarak) gönderin."
        )

@bot.message_handler(content_types=['text', 'photo', 'document'])
def handle_payment_or_proof(message):
    chat_id = message.chat.id
    country_id = user_countries.get(chat_id, "0")
    
    bot.reply_to(message, "Dekont / Ödeme alındı! Onaylanıyor ve sistemden numara talep ediliyor, lütfen bekleyin...")
    
    try:
        url = f"https://onaylasms.com.tr/stubs/handler_api.php?api_key={API_KEY}&action=getNumber&service=wa&country={country_id}"
        response = requests.get(url, timeout=15)
        res_text = response.text.strip()
        
        if "ACCESS_NUMBER" in res_text:
            parts = res_text.split(":")
            activation_id = parts[1]
            phone_number = parts[2]
            bot.reply_to(message, f"Numara başarıyla alındı!\nNumara: +{phone_number}\nİşlem ID: {activation_id}")
        else:
            bot.reply_to(message, f"API'den numara alınamadı. Sağlayıcı yanıtı: {res_text}")
    except Exception as e:
        bot.reply_to(message, f"Bağlantı hatası oluştu: {str(e)}")

if __name__ == "__main__":
    # Flask sunucusunu ayrı bir arkaplanda (thread) başlat
    t = threading.Thread(target=run_flask)
    t.start()
    
    # Telegram botunu başlat
    bot.remove_webhook()
    bot.infinity_polling()
