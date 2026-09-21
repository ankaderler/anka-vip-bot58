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

# Kendi Telegram Kullanıcı ID'ni buraya yaz (Dekontlar onay için sana gelecek)
ADMIN_CHAT_ID = 123456789  # <-- Buraya kendi Telegram ID'ni yazmalısın!

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
    # Butonların yanına fiyatlar eklendi (Fiyatları dilediğin gibi değiştirebilirsin)
    markup.add(InlineKeyboardButton("🇹🇷 Türkiye - WhatsApp (150 TL)", callback_data="sel_wa_0"))
    markup.add(InlineKeyboardButton("🇬🇧 İngiltere - WhatsApp (150 TL)", callback_data="sel_wa_16"))
    markup.add(InlineKeyboardButton("🇺🇸 Amerika - Telegram (150 TL)", callback_data="sel_tg_12"))
    markup.add(InlineKeyboardButton("🇹🇷 Türkiye - Telegram (150 TL)", callback_data="sel_tg_0"))
    
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
        service = parts[1]      
        country_id = parts[2]   
        
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
        
    elif data.startswith("approve_") or data.startswith("reject_"):
        action, target_user_str = data.split("_")
        target_user_id = int(target_user_str)
        
        if action == "approve":
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=call.message.text + "\n\n✅ **ÖDEME ONAYLANDI**"
            )
            bot.send_message(target_user_id, "✅ Dekontunuz onaylandı! Sistemden numara talep ediliyor, lütfen bekleyin...")
            
            selection = user_selections.get(target_user_id, {"service": "wa", "country": "0"})
            process_number_request(target_user_id, selection["service"], selection["country"])
            
        else:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=call.message.text + "\n\n❌ **ÖDEME REDDEDİLDİ (Sahte/Geçersiz Dekont)**"
            )
            bot.send_message(target_user_id, "❌ Gönderdiğiniz dekont geçersiz veya onaylanmadı. Lütfen geçerli bir dekont iletin.")

def check_sms_loop(chat_id, activation_id):
    start_time = time.time()
    while time.time() - start_time < 300:
        try:
            status_url = f"https://onaylasms.com.tr/stubs/handler_api.php?api_key={API_KEY}&action=getStatus&id={activation_id}"
            resp = requests.get(status_url, timeout=10)
            res_text = resp.text.strip()
            
            if "STATUS_OK" in res_text:
                code = res_text.split(":")[-1]
                bot.send_message(chat_id, f"✅ **SMS Kodu Geldi!**\n\n🔑 Kodunuz: `{code}`", parse_mode="Markdown")
                return
            elif "STATUS_CANCEL" in res_text:
                bot.send_message(chat_id, "❌ İşlem iptal edildi veya süre aşımına uğradı.")
                return
        except Exception:
            pass
        
        time.sleep(5)
        
    bot.send_message(chat_id, "⏳ 5 dakika içinde kod gelmediği için işlem zaman aşımına uğradı.")

def process_number_request(chat_id, service, country_id):
    try:
        url = f"https://onaylasms.com.tr/stubs/handler_api.php?api_key={API_KEY}&action=getNumber&service={service}&country={country_id}"
        response = requests.get(url, timeout=15)
        res_text = response.text.strip()
        
        if "ACCESS_NUMBER" in res_text:
            parts = res_text.split(":")
            activation_id = parts[1]
            phone_number = parts[2]
            
            bot.send_message(chat_id, f"Numara başarıyla alındı!\nNumara: +{phone_number}\nİşlem ID: {activation_id}\n\n⏳ SMS kodu bekleniyor, kod geldiğinde buraya otomatik olarak yazılacak...")
            
            sms_thread = threading.Thread(target=check_sms_loop, args=(chat_id, activation_id))
            sms_thread.start()
        else:
            bot.send_message(chat_id, f"⚠️ Numara alınamadı!\nSağlayıcı Yanıtı: `{res_text}`\n\nLütfen bakiyenizi veya sağlayıcıdaki stok durumunu kontrol edin.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"Bağlantı hatası oluştu: {str(e)}")

@bot.message_handler(content_types=['text', 'photo', 'document'])
def handle_payment_or_proof(message):
    chat_id = message.chat.id
    
    if ADMIN_CHAT_ID and chat_id != ADMIN_CHAT_ID:
        user_name = message.from_user.first_name or "Kullanıcı"
        username = f"@{message.from_user.username}" if message.from_user.username else "Yok"
        
        bot.reply_to(message, "Dekontunuz alındı! Yönetici onayına gönderildi, lütfen onay bekleniyor...")
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ Onayla", callback_data=f"approve_{chat_id}"),
            InlineKeyboardButton("❌ Reddet", callback_data=f"reject_{chat_id}")
        )
        
        caption = f"🔔 **Yeni Ödeme Bildirimi!**\n\nMüşteri: {user_name} ({username})\nChat ID: {chat_id}"
        
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            bot.send_photo(ADMIN_CHAT_ID, file_id, caption=caption, reply_markup=markup, parse_mode="Markdown")
        elif message.content_type == 'document':
            file_id = message.document.file_id
            bot.send_document(ADMIN_CHAT_ID, file_id, caption=caption, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(ADMIN_CHAT_ID, f"{caption}\n\nMetin içeriği: {message.text}", reply_markup=markup, parse_mode="Markdown")
    else:
        if chat_id == ADMIN_CHAT_ID:
            bot.reply_to(message, "Yönetim paneli: Buraya dekont göndermeyin, müşterilerin dekontları size onay için gelecektir.")

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
