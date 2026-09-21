import os
import time
import threading
import requests
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Yapılandırma Bilgileri
TOKEN = "8966819189:AAFhWDClW5LfI1UQeKZqhgu8C8OCR-qjqzY"
API_KEY = "osms_78764ab234637198f606b1bb0ce55ced58aabbb2f1be18b3"
TARGET_NAME = "Resul Sakal"
IBAN = "TR62 0006 2000 5000 0006 8107 73"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_selections = {}

@app.route('/')
def home():
    return "ANGA VIP SERVICES Bot Aktif ve Calisiyor!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🇹🇷 Türkiye - WhatsApp", callback_data="sel_wa_0"))
    markup.add(InlineKeyboardButton("🇬🇧 İngiltere - WhatsApp", callback_data="sel_wa_16"))
    markup.add(InlineKeyboardButton("🇺🇸 Amerika - Telegram", callback_data="sel_tg_12"))
    markup.add(InlineKeyboardButton("🇹🇷 Türkiye - Telegram", callback_data="sel_tg_0"))
    
    bot.send_message(
        message.chat.id, 
        "ANGA VIP SERVICES Bot aktif!\n\nLütfen almak istediğiniz hizmeti seçin:", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    bot.answer_callback_query(call.id)
    
    if data.startswith("sel_"):
        parts = data.split("_")
        service = parts[1]      # wa veya tg
        country_id = parts[2]   # 0, 12, 16
        
        user_selections[call.message.chat.id] = {
            "service": service,
            "country": country_id
        }
        
        c_names = {"0": "Türkiye", "12": "Amerika", "16": "İngiltere"}
        s_names = {"wa": "WhatsApp", "tg": "Telegram"}
        
        c_name = c_names.get(country_id, "Türkiye")
        s_name = s_names.get(service, "WhatsApp")
        
        bot.send_message(
            call.message.chat.id, 
            f"Seçilen Ürün: {c_name} - {s_name}\nTutar: 150 TL\n\n"
            f"📌 Ödeme Bildirimi:\n"
            f"Alıcı: {TARGET_NAME}\n"
            f"IBAN: {IBAN}\n\n"
            f"Lütfen yukarıdaki IBAN'a ödemeyi yaptıktan sonra dekontu (fotoğraf veya dosya olarak) gönderin."
        )

# SMS kodunu arka planda periyodik olarak kontrol eden fonksiyon
def check_sms_loop(chat_id, activation_id):
    start_time = time.time()
    # 5 dakika (300 saniye) boyunca kodu aramaya devam eder
    while time.time() - start_time < 300:
        try:
            status_url = f"https://onaylasms.com.tr/stubs/handler_api.php?api_key={API_KEY}&action=getStatus&id={activation_id}"
            resp = requests.get(status_url, timeout=10)
            res_text = resp.text.strip()
            
            if "STATUS_OK" in res_text:
                # Örnek yanıt: STATUS_OK:123456
                code = res_text.split(":")[-1]
                bot.send_message(chat_id, f"✅ **SMS Kodu Geldi!**\n\n🔑 Kodunuz: `{code}`", parse_mode="Markdown")
                return
            elif "STATUS_CANCEL" in res_text:
                bot.send_message(chat_id, "❌ İşlem iptal edildi veya süre aşımına uğradı.")
                return
        except Exception:
            pass
        
        time.sleep(5) # Her 5 saniyede bir kontrol et
        
    bot.send_message(chat_id, "⏳ 5 dakika içinde kod gelmediği için işlem zaman aşımına uğradı.")

@bot.message_handler(content_types=['text', 'photo', 'document'])
def handle_payment_or_proof(message):
    chat_id = message.chat.id
    selection = user_selections.get(chat_id, {"service": "wa", "country": "0"})
    
    service = selection["service"]
    country_id = selection["country"]
    
    bot.reply_to(message, "Dekont / Ödeme alındı! Onaylanıyor ve sistemden numara talep ediliyor, lütfen bekleyin...")
    
    try:
        url = f"https://onaylasms.com.tr/stubs/handler_api.php?api_key={API_KEY}&action=getNumber&service={service}&country={country_id}"
        response = requests.get(url, timeout=15)
        res_text = response.text.strip()
        
        if "ACCESS_NUMBER" in res_text:
            parts = res_text.split(":")
            activation_id = parts[1]
            phone_number = parts[2]
            
            bot.reply_to(message, f"Numara başarıyla alındı!\nNumara: +{phone_number}\nİşlem ID: {activation_id}\n\n⏳ SMS kodu bekleniyor, kod geldiğinde buraya otomatik olarak yazılacak...")
            
            # SMS kontrolünü ayrı bir iş parçacığında (thread) başlat
            sms_thread = threading.Thread(target=check_sms_loop, args=(chat_id, activation_id))
            sms_thread.start()
        else:
            bot.reply_to(message, f"API'den numara alınamadı. Sağlayıcı yanıtı: {res_text}")
    except Exception as e:
        bot.reply_to(message, f"Bağlantı hatası oluştu: {str(e)}")

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception:
        pass
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Polling hatası yeniden bağlanıyor: {e}")
            time.sleep(3)
