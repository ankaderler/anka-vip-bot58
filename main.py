import os
import time
import threading
import requests
import telebot
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8966819189:AAENmHdrI8XxNexWFsaAqyfHZn7kxi0N-CQ"
API_KEY = "osms_686d5d570f17954f960c7f4411bf87edecf774e806a423a7"
TARGET_NAME = "Resul Sakal"
IBAN = "TR62 0006 2000 5000 0006 8107 73"
SUPPORT_USERNAME = "@SMSPATRONUM"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_selections = {}
user_activations = {}

@app.route('/')
def home():
    return "ANKA VIP SERVICES Bot Aktif ve Calisiyor!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🇹🇷 Türkiye - WhatsApp (300 TL)", callback_data="sel_wa_0"))
    markup.add(InlineKeyboardButton("🇬🇧 İngiltere - WhatsApp (150 TL)", callback_data="sel_wa_16"))
    markup.add(InlineKeyboardButton("🇺🇸 Amerika - Telegram (150 TL)", callback_data="sel_tg_12"))
    markup.add(InlineKeyboardButton("🇹🇷 Türkiye - Telegram (200 TL)", callback_data="sel_tg_0"))
    markup.add(InlineKeyboardButton("💬 Canlı Destek / İletişim: @SMSPATRONUM", url="https://t.me/SMSPATRONUM"))
    
    bot.send_message(
        chat_id, 
        "ANKA VIP SERVICES Bot aktif!\n\nLütfen almak istediğiniz hizmeti seçin:", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document', 'audio', 'video', 'sticker'])
def handle_incoming_messages(message):
    chat_id = message.chat.id
    text = message.text if message.text else ""
    
    if text.startswith('/'):
        return

    if chat_id not in user_selections:
        user_selections[chat_id] = {"service": "tg", "country": "0"}

    selection = user_selections[chat_id]
    service = selection["service"]
    country_id = selection["country"]
    
    bot.reply_to(message, "🔄 Dekont alındı, numara hazırlanıyor...")
    fetch_and_send_number(chat_id, service, country_id, is_replacement=False)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data
    chat_id = call.message.chat.id
    
    if data.startswith("sel_"):
        bot.answer_callback_query(call.id)
        parts = data.split("_")
        service = parts[1]      
        country_id = parts[2]   
        
        user_selections[chat_id] = {
            "service": service,
            "country": country_id
        }
        
        c_names = {"0": "Türkiye", "12": "Amerika", "16": "İngiltere"}
        s_names = {"wa": "WhatsApp", "tg": "Telegram"}
        
        c_name = c_names.get(country_id, "Türkiye")
        s_name = s_names.get(service, "WhatsApp")
        
        prices = {
            ("wa", "0"): "300 TL",
            ("wa", "16"): "150 TL",
            ("tg", "12"): "150 TL",
            ("tg", "0"): "200 TL"
        }
        price = prices.get((service, country_id), "150 TL")
        
        bot.send_message(
            chat_id, 
            f"Seçilen Ürün: {c_name} - {s_name}\nTutar: {price}\n\n"
            f"📌 Ödeme Bildirimi:\n"
            f"Alıcı: {TARGET_NAME}\n"
            f"IBAN: {IBAN}\n\n"
            f"Lütfen yukarıdaki IBAN'a ödemeyi yaptıktan sonra dekontu (fotoğraf veya dosya olarak) gönderin.\n\n"
            f"💬 **Canlı Destek:** {SUPPORT_USERNAME}",
            parse_mode="Markdown"
        )
        
    elif data == "change_number":
        bot.answer_callback_query(call.id, "Eski numara iptal ediliyor ve yeni numara alınıyor...")
        
        if chat_id not in user_activations:
            bot.send_message(chat_id, f"Aktif numaranız bulunamadı. Destek: {SUPPORT_USERNAME}")
            return
            
        old_activation_id = user_activations[chat_id]
        
        try:
            cancel_url = f"https://onaylasms.com.tr/stubs/handler_api.php?api_key={API_KEY}&action=setStatus&status=8&id={old_activation_id}"
            requests.get(cancel_url, timeout=5)
        except Exception:
            pass
            
        selection = user_selections.get(chat_id, {"service": "wa", "country": "16"})
        service = selection["service"]
        country_id = selection["country"]
        
        fetch_and_send_number(chat_id, service, country_id, is_replacement=True)

def check_sms_loop(chat_id, activation_id):
    start_time = time.time()
    while time.time() - start_time < 300:
        if user_activations.get(chat_id) != activation_id:
            return
            
        try:
            status_url = f"https://onaylasms.com.tr/stubs/handler_api.php?api_key={API_KEY}&action=getStatus&id={activation_id}"
            resp = requests.get(status_url, timeout=5)
            res_text = resp.text.strip()
            
            if "STATUS_OK" in res_text:
                code = res_text.split(":")[-1]
                bot.send_message(chat_id, f"✅ **SMS Kodu Geldi!**\n\n🔑 Kodunuz: `{code}`\n\n💬 İletişim / Destek: {SUPPORT_USERNAME}", parse_mode="Markdown")
                return
            elif "STATUS_CANCEL" in res_text:
                return
        except Exception:
            pass
        
        time.sleep(5)

def fetch_and_send_number(chat_id, service, country_id, is_replacement=False):
    phone_number = None
    activation_id = None
    
    # Denenecek alternatifler listesi (Önce istenen, sonra yabancı ve uygun alternatifler)
    try_list = [(service, country_id), ("wa", "16"), ("tg", "12"), ("wa", "0"), ("tg", "0")]
    
    for s_srv, s_cnt in try_list:
        try:
            url = f"https://onaylasms.com.tr/stubs/handler_api.php?api_key={API_KEY}&action=getNumber&service={s_srv}&country={s_cnt}"
            response = requests.get(url, timeout=10)
            res_text = response.text.strip()
            print(f"API Deneme ({s_srv}, {s_cnt}): {res_text}")
            
            if "ACCESS_NUMBER" in res_text:
                parts = res_text.split(":")
                activation_id = parts[1]
                phone_number = parts[2]
                break
        except Exception:
            continue

    if phone_number and activation_id:
        user_activations[chat_id] = activation_id
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔄 Kod Gelmedi / Numara Değiştir", callback_data="change_number"))
        markup.add(InlineKeyboardButton("💬 Canlı Destek ile İletişim", url="https://t.me/SMSPATRONUM"))
        
        prefix_text = "🔄 **Yeni Numaranız Hazırlandı!**\n\n" if is_replacement else "✅ **Dekont onaylandı, numaranız alındı!**\n\n"
        
        bot.send_message(
            chat_id, 
            f"{prefix_text}"
            f"Numara: +{phone_number}\n"
            f"İşlem ID: {activation_id}\n\n"
            f"⏳ SMS kodu bekleniyor...\n\n"
            f"💬 **İletişim / Destek:** {SUPPORT_USERNAME}", 
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
        sms_thread = threading.Thread(target=check_sms_loop, args=(chat_id, activation_id))
        sms_thread.start()
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💬 Canlı Destek ile Bağlan", url="https://t.me/SMSPATRONUM"))
        bot.send_message(
            chat_id, 
            f"✅ **Dekontunuz onaylandı!**\n\n"
            f"⚠️ Anlık yoğunluk nedeniyle alternatif havuzda da numara kalmadı. Lütfen hemen canlı destekten numaranızı isteyin:\n\n"
            f"💬 **İletişim / Destek:** {SUPPORT_USERNAME}",
            reply_markup=markup,
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True", timeout=10)
        time.sleep(2)
    except Exception:
        pass
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20, skip_pending=True)
        except Exception as e:
            print(f"Polling hatası yeniden bağlanıyor: {e}")
            time.sleep(3)
