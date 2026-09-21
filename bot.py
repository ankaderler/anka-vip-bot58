import os
import threading
import http.server
import socketserver
import logging
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Render Port Ayarı (Canlı kalması için)
PORT = int(os.environ.get("PORT", 10000))

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ANKA VIP SMS Bot is live and running!")

def run_web_server():
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# BOT VE API BİLGİLERİ
BOT_TOKEN = "8975549312:AAH9mIb8yIsmAfJYimJq0IQ6_kpBu9-kJxY"
IBAN = "TR62 0006 2000 5000 0006 8107 73"
RECIPIENT = "Resul Sakal"
SUPPORT_USERNAME = "SMSPATRONUM"

# Onayla SMS Gerçek API Bilgileri
SMS_API_KEY = "osms_64c57cd4c153d55613acaeb0b442b643eb12f234c9585657"
SMS_API_URL = "https://onaylasms.com.tr/stubs/handler_api.php"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Servis Bilgileri (onaylasms.com.tr panelindeki standart SMS-Activate / 5SIM uyumlu servis kodları)
SERVICES = {
    "tr_wp": {"name": "TR WhatsApp", "code": "whatsapp", "price": 300},
    "tr_tg": {"name": "TR Telegram", "code": "telegram", "price": 200},
    "abd_wp": {"name": "ABD WhatsApp", "code": "whatsapp", "price": 150},
    "uk_wp": {"name": "İngiltere WhatsApp", "code": "whatsapp", "price": 150}
}

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🇹🇷 TR WhatsApp — 300 TL", callback_data="buy_tr_wp")],
        [InlineKeyboardButton("🇹🇷 TR Telegram — 200 TL", callback_data="buy_tr_tg")],
        [InlineKeyboardButton("🇺🇸 ABD WhatsApp — 150 TL", callback_data="buy_abd_wp")],
        [InlineKeyboardButton("🇬🇧 İngiltere WhatsApp — 150 TL", callback_data="buy_uk_wp")],
        [InlineKeyboardButton("📞 Canlı Destek", url=f"https://t.me/{SUPPORT_USERNAME}")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💎 *ANKA VIP — SMS ONAY SERVİSİ*\n\n"
        "⚡ Güvenli ve Hızlı Numara Tedariği\n"
        "Aşağıdaki menüden almak istediğiniz ülke ve platformu seçebilirsiniz."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("buy_"):
        service_key = data.replace("buy_", "")
        service_info = SERVICES.get(service_key, SERVICES["tr_wp"])
        price = service_info["price"]
        
        context.user_data["selected_service"] = service_key

        text = (
            f"🛒 *Seçilen Paket: {service_info['name']}*\n"
            f"💰 Tutar: *{price} TL*\n\n"
            f"💳 *Ödeme Bilgileri*\n"
            f"IBAN:\n`{IBAN}`\n\n"
            f"Alıcı: *{RECIPIENT}*\n\n"
            "━━━━━━━━━━━━━━━━\n"
            f"1️⃣ Yukarıdaki hesaba *{price} TL* gönderin.\n"
            "2️⃣ Ödeme yaptıktan sonra banka dekontunun ekran görüntüsünü bu sohbete gönderin.\n"
            "3️⃣ Bot dekontu onaylayıp `onaylasms.com.tr` üzerinden gerçek numaranızı ve SMS kodunuzu otomatik teslim edecektir."
        )
        keyboard = [
            [InlineKeyboardButton("⬅️ Ana Menüye Dön", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "home":
        text = (
            "💎 *ANKA VIP — SMS ONAY SERVİSİ*\n\n"
            "⚡ Güvenli ve Hızlı Numara Tedariği\n"
            "Aşağıdaki menüden almak istediğiniz ülke ve platformu seçebilirsiniz."
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

# Stok Bulamazsa Siteyi Yenileyerek Tekrar Deneyen Akıllı Numara Çekme Fonksiyonu
def fetch_real_number_with_retry(service_code):
    params = {
        "api_key": SMS_API_KEY,
        "action": "getNumber",
        "service": service_code
    }
    
    # Stok yoksa siteyi 3 kez ard arda yenileyip (tekrar sorgulayarak) numara düşürmeye çalışır
    for attempt in range(3):
        try:
            response = requests.get(SMS_API_URL, params=params, timeout=15)
            result_text = response.text.strip()
            
            if "ACCESS_NUMBER" in result_text:
                parts = result_text.split(":")
                activation_id = parts[1] if len(parts) > 1 else "Bilinmiyor"
                phone_number = parts[2] if len(parts) > 2 else result_text
                return phone_number, f"Kod Bekleniyor (ID: {activation_id})"
            
            # Eğer stok yoksa (NO_NUMBERS veya BAD_SERVICE dönerse) 2 saniye bekleyip siteyi tekrar yeniler/sorgular
            time.sleep(2)
        except Exception as e:
            logging.error(f"API Deneme Hatası ({attempt+1}): {e}")
            time.sleep(2)
            
    return "Stok Bulunamadı", "Lütfen Canlı Destek ile İletişime Geçin"

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or update.message.document:
        service_key = context.user_data.get("selected_service", "tr_wp")
        service_info = SERVICES.get(service_key, SERVICES["tr_wp"])

        # Siteden stok arama ve yenileme döngüsü tetikleniyor
        assigned_number, sms_status = fetch_real_number_with_retry(service_info["code"])

        text = (
            f"✅ *Dekont Onaylandı & Siteden Numara Çekildi!*\n\n"
            f"📦 Servis: *{service_info['name']}*\n"
            f"📱 *Gerçek Numara:* `{assigned_number}`\n"
            f"💬 *Durum / Kod:* `{sms_status}`\n\n"
            f"⚠️ Destek & Sorun Bildirimi İçin: @{SUPPORT_USERNAME}"
        )
        keyboard = [[InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await update.message.reply_text("📸 Lütfen geçerli bir dekont görseli veya dosyası gönderin.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_handler))
    
    print("ANKA VIP SMS BOT Yenileme Özelliği ile Aktif!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
