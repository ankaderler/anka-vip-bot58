import os
import threading
import http.server
import socketserver
import logging
import httpx
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
        self.wfile.write(b"ANKA Sorgu Bot is running perfectly!")

def run_web_server():
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        httpd.serve_forever()

# Arka planda web sunucusunu başlatıyoruz (Render / Koyeb uyumlu)
threading.Thread(target=run_web_server, daemon=True).start()

# Yeni Token
BOT_TOKEN = "8874989367:AAFeyFjKEn4g5Rp45EC0nym-1yCFOCbEcbc" 

# Sitenizdeki sorgu scriptinin adresi (Burayı kendi sitenize göre güncelleyin)
SORGULA_URL = "https://sitenizinadresi.com/sorgula.php"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🔍 Sorgulama Yap", callback_data="start_query")],
        [InlineKeyboardButton("📞 Destek", url="https://t.me/SMSPATRONUM")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = (
            "🔍 *ANKA GERÇEK SORGU PANELİ*\n\n"
            "Aşağıdaki butona basarak aratmak istediğiniz ismi veya bilgiyi gönderebilirsiniz."
        )
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
        elif update.callback_query:
            await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        logging.error(f"Start komutu hatası: {e}")

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message and update.message.text:
            user_text = update.message.text.strip()
            
            # Eğer kullanıcı sorgu modunu bekliyorsa
            if context.user_data.get("waiting_for_query"):
                context.user_data["waiting_for_query"] = False
                await execute_query(update, context, user_text)
                return

            text = (
                "🔍 *ANKA GERÇEK SORGU PANELİ*\n\n"
                "Lütfen sorgulama yapmak için aşağıdaki butonu kullanın."
            )
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        logging.error(f"Metin mesajı işleme hatası: {e}")

async def execute_query(update: Update, context: ContextTypes.DEFAULT_TYPE, aranan: str):
    msg = await update.message.reply_text(f"🔍 `{aranan}` için sorgu paneli taranıyor, lütfen bekleyin...")
    
    params = {"arama": aranan}
    headers = {"User-Agent": "Mozilla/5.0"}
    
    async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
        try:
            response = await client.get(SORGULA_URL, params=params)
            result_text = response.text.strip()
            
            if not result_text:
                result_text = "⚠️ Bu arama için veritabanında sonuç bulunamadı."
            
            # Telegram mesaj karakter sınırına göre kırpma (4000 karakter)
            if len(result_text) > 4000:
                result_text = result_text[:4000] + "\n\n... (Sonuç çok uzun olduğu için kesildi)"

            text = f"📊 *SORGU SONUCU:*\n\n```text\n{result_text}\n```"
            keyboard = [
                [InlineKeyboardButton("🔍 Yeni Sorgu Yap", callback_data="start_query")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]
            ]
            await msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logging.error(f"Sorgu API Hatası: {e}")
            keyboard = [[InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]]
            await msg.edit_text(f"❌ Sorgu sunucusuna bağlanırken bir hata oluştu.\nDetay: {e}", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data == "start_query":
            context.user_data["waiting_for_query"] = True
            text = (
                "🔍 *GERÇEK SORGU PANELİ*\n\n"
                "Lütfen sorgulamak istediğiniz **İsim Soyisim** veya bilgiyi **şimdi mesaja yazıp gönderin**."
            )
            keyboard = [[InlineKeyboardButton("⬅️ Ana Menüye Dön", callback_data="home")]]
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

        elif data == "home":
            context.user_data["waiting_for_query"] = False
            text = (
                "🔍 *ANKA GERÇEK SORGU PANELİ*\n\n"
                "Aşağıdaki butona basarak aratmak istediğiniz ismi veya bilgiyi gönderebilirsiniz."
            )
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        logging.error(f"Buton işleme hatası: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    
    print("Sadece Sorgu Paneli Olan Bot Aktif Edildi ve Dinlemede!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
