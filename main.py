import os
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Yapılandırma Bilgileri
TOKEN = "8638410333:AAFfehwYD3v2iPDkI5XygDadjEph2KQ0u_k"
API_KEY = "sms_78764ab234637198f606b1bb0ce55ced58aabbb2f1be18b3"
TARGET_NAME = "Resul Sakal"
IBAN = "TR62 0006 2000 5000 0006 8107 73"

bot = telebot.TeleBot(TOKEN)

# Kullanıcıların seçtiği ülkeleri hafızada tutmak için sözlük
user_countries = {}

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

# Fotoğraf, dosya (PDF) veya metin türündeki tüm ödeme bildirimlerini hatasız yakalar
@bot.message_handler(content_types=['text', 'photo', 'document'])
def handle_payment_or_proof(message):
    chat_id = message.chat.id
    country_id = user_countries.get(chat_id, "0") # Varsayılan Türkiye
    
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
    bot.remove_webhook()
    bot.infinity_polling()
