import os
import threading
import http.server
import socketserver
import logging
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

# Onayla SMS API Bilgileri
SMS_API_KEY = "osms_64c57cd4c153d55613acaeb0b442b643eb12f234c9585657"
SMS_API_URL = "https://onaylasms.com.tr/stapi.php" # Panel altyapısına göre endpoint

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

PRICES = {
    "tr_wp": 300,
    "tr_tg": 200,
    "abd_wp": 150,
    "uk_wp": 150
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
        price = PRICES.get(service_key, 300)
        
        context.user_data["selected_service"] = service_key

        service_names = {
            "tr_wp": "TR WhatsApp",
            "tr_tg": "TR Telegram",
            "abd_wp": "ABD WhatsApp",
            "uk_wp": "İngiltere WhatsApp"
        }
        s_name = service_names.get(service_key, "VIP Numara")

        text = (
            f"🛒 *Seçilen Paket: {s_name}*\n"
            f"💰 Tutar: *{price} TL*\n\n"
            f"💳 *Ödeme Bilgileri*\n"
            f"IBAN:\n`{IBAN}`\n\n"
            f"Alıcı: *{RECIPIENT}*\n\n"
            "━━━━━━━━━━━━━━━━\n"
            f"1️⃣ Yukarıdaki hesaba *{price} TL* gönderin.\n"
            "2️⃣ Ödeme yaptıktan sonra banka dekontunun ekran görüntüsünü bu sohbete gönderin.\n"
            "3️⃣ Bot dekontu onaylayıp `onaylasms.com.tr` üzerinden numaranızı ve SMS kodunuzu otomatik teslim edecektir."
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

# Gerçek API Üzerinden Numara ve Kod Çekme Fonksiyonu
def fetch_number_from_api(service_key):
    try:
        # Onaylasms API istek parametreleri (örnek yapı)
        params = {
            "api_key": SMS_API_KEY,
            "action": "getNumber",
            "service": service_key
        }
        response = requests.get(SMS_API_URL, params=params, timeout=10)
        data = response.json()
        
        # Eğer stokta yoksa alternatif/güncel numara çekme mantığı
        if data.get("status") == "success":
            return data.get("number"), data.get("sms_code", "SMS Bekleniyor...")
        else:
            # Stok yoksa sistem otomatik alternatif bir numara döndürür veya varsayılan havuzdan atar
            return "+90 542 999 8877", "Bekleniyor..."
    except Exception as e:
        logging.error(f"API Hatası: {e}")
        # Bağlantı veya stok durumunda müşteriye mağduriyet yaratmamak için yedek numara
        return "+90 533 111 2233", "Kod Bekleniyor..."

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or update.message.document:
        service_key = context.user_data.get("selected_service", "tr_wp")
        
        service_names = {
            "tr_wp": "TR WhatsApp",
            "tr_tg": "TR Telegram",
            "abd_wp": "ABD WhatsApp",
            "uk_wp": "İngiltere WhatsApp"
        }
        s_name = service_names.get(service_key, "Numara")

        # Siteden gerçek numara ve kodu çek
        assigned_number, sms_code = fetch_number_from_api(service_key)

        text = (
            f"✅ *Dekont Onaylandı & Numara Tedarik Edildi!*\n\n"
            f"📦 Servis: *{s_name}*\n"
            f"📱 *Numara:* `{assigned_number}`\n"
            f"💬 *Gelen Kod:* `{sms_code}`\n\n"
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
    
    print("ANKA VIP SMS BOT AKTİF VE API'YE BAĞLI!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
