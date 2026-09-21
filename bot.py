import os
import threading
import http.server
import socketserver
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

PORT = int(os.environ.get("PORT", 10000))

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ANKA VIP Bot is live and running!")

def run_web_server():
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

BOT_TOKEN = "8522565760:AAEB0cxhpm8LX7VnIsfAfED0IYkDI5Rf45w"
IBAN = "TR06 0001 0021 5470 2002 4550 04"
RECIPIENT = "Zeynep Alkoç"

LINKS = [
    "https://t.me/+Aqi4UqSzr4JjZmRk",
    "https://t.me/+H2z-xlyZ6zM0OTE0",
    "https://t.me/+p01bQp6XebkzMmI0",
    "https://t.me/+HqtuwLtoMkkwMWQ0",
    "https://t.me/+BcHhS86B9ocyMWQ0",
]

SUPPORT_USERNAME = "ANKA"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🛒 VIP Paket Satın Al — 300 TL", callback_data="buy")],
        [InlineKeyboardButton("📖 Nasıl Satın Alacağım?", callback_data="how")],
        [InlineKeyboardButton("📦 Ürün Bilgileri", callback_data="info")],
        [InlineKeyboardButton("📞 Destek", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💎 *ANKA VIP*\n\n"
        "🔐 Özel VIP erişim paketi\n"
        "⚡ Hızlı dijital teslimat\n"
        "💰 Paket fiyatı: *300 TL*\n\n"
        "Aşağıdaki menüden işlem yapmak istediğiniz seçeneği seçebilirsiniz."
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        text = (
            "🛒 *VIP PAKET SATIN AL*\n\n"
            "💰 Fiyat: *300 TL*\n\n"
            "💳 *Ödeme Bilgileri*\n\n"
            f"IBAN:\n`{IBAN}`\n\n"
            f"Alıcı: *{RECIPIENT}*\n\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "1️⃣ Yukarıdaki hesaba *300 TL* gönderin.\n"
            "2️⃣ Ödeme yaptıktan sonra dekontunuzu bu bota gönderin.\n"
            "3️⃣ Ödeme doğrulaması tamamlandığında VIP erişiminiz teslim edilir."
        )
        keyboard = [
            [InlineKeyboardButton("📸 DEKONT GÖNDERECEĞİM", callback_data="receipt")],
            [InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "how":
        text = (
            "📖 *NASIL SATIN ALACAKSINIZ?*\n\n"
            "1️⃣ *VIP Paket Satın Al* butonuna basın.\n"
            "2️⃣ Size gösterilen IBAN'a *300 TL* gönderin.\n"
            "3️⃣ Ödeme yaptıktan sonra dekontunuzu bota gönderin.\n"
            "4️⃣ Ödeme doğrulandığında VIP erişim linkleriniz teslim edilir. 🔐"
        )
        keyboard = [
            [InlineKeyboardButton("🛒 HEMEN SATIN AL", callback_data="buy")],
            [InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "info":
        text = (
            "📦 *VIP ÜRÜN BİLGİLERİ*\n\n"
            "💎 VIP Paket\n"
            "🔗 5 adet VIP erişim\n"
            "💰 Fiyat: *300 TL*\n"
            "⚡ Dijital teslimat"
        )
        keyboard = [
            [InlineKeyboardButton("🛒 SATIN AL", callback_data="buy")],
            [InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "receipt":
        text = (
            "📸 *DEKONT GÖNDERME*\n\n"
            "Ödemeyi yaptıktan sonra banka dekontunuzun ekran görüntüsünü veya PDF dosyasını bu sohbete gönderin."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Geri", callback_data="buy")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "support":
        text = f"📞 *DESTEK*\n\nDestek için: @{SUPPORT_USERNAME}"
        keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "home":
        text = "💎 *ANKA VIP*\n\nPaket fiyatı: *300 TL*\nİşlem seçin:"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or update.message.document:
        keyboard = [
            [InlineKeyboardButton("🔗 VIP 1'e Katıl", url=LINKS[0])],
            [InlineKeyboardButton("🔗 VIP 2'ye Katıl", url=LINKS[1])],
            [InlineKeyboardButton("🔗 VIP 3'e Katıl", url=LINKS[2])],
            [InlineKeyboardButton("🔗 VIP 4'e Katıl", url=LINKS[3])],
            [InlineKeyboardButton("🔗 VIP 5'e Katıl", url=LINKS[4])],
        ]
        await update.message.reply_text(
            "🎉 *Dekont Alındı ve Onaylandı!* VIP erişimleriniz aşağıdadır:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    await update.message.reply_text("📸 Lütfen banka dekontunun fotoğrafını veya PDF dosyasını gönderin.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_handler))
    
    print("ANKA VIP BOT AKTİF!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
