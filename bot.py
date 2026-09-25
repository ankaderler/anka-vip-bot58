rt logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Logging ayarları
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Token
TOKEN = "8659358008:AAHFKg3notOSzpqFfZv7ibkocs4e3ixYMOY"

# Ödeme Bilgileri
IBAN = "TR06 0001 0021 5470 2002 4550 04"
ALICI_ADI = "Zeynep Alkoç"
TUTAR = "400 TL"

# Teslim edilecek VIP Linkler
VIP_LINKLER = (
    "🎉 **Ödemeniz Onaylandı!** 🎉\n\n"
    "İşte Zeynep VIP Arşivi ve Özel Linkleriniz:\n"
    "🔗 [Arşivi Görüntüle ve İndir](https://t.me/+orneklinkiniz)\n\n"
    "🎁 **Hediye:** 20 Dakika Ücretsiz Şov Hakkınız tanımlanmıştır!"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_name = update.effective_user.first_name
  text = (
      f"⭐ Merhaba **{user_name}**, Zeynep'in Arşivi için ödeme bilgileri"
      f" aşağıdadır:\n\n"
      f"👤 Alıcı: **{ALICI_ADI}**\n"
      f"💳 IBAN: `{IBAN}`\n"
      f"💰 Tutar: **{TUTAR}**\n\n"
      "🎁 *Not:* Arşivi alan herkese **20 dk show ücretsizdir!**\n\n"
'Ödemeyi yaptıktan sonra dekontunuzun ekran görüntüsünü "fotoğraf" olarak'
      " bu sohbete gönderin."
  )
  await update.message.reply_text(text, parse_mode="Markdown")


async def foto_veya_belge_geldi(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  user = update.effective_user
  keyboard = [[
      InlineKeyboardButton(
          f"✅ Onayla ve Link Ver ({user.id})",
          callback_data=f"onayla_{user.id}",
      )
  ]]
  reply_markup = InlineKeyboardMarkup(keyboard)

  # Dekontu size (yöneticiye) veya sohbete bildirir
  await update.message.reply_text(
      "⏳ Dekontunuz alındı! Yönetici kontrol ediyor, onaylandığı an linkler"
      " gelecektir.",
      reply_markup=reply_markup,
  )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  data = query.data
  if data.startswith("onayla_"):
    hedef_user_id = int(data.split("_")[1])

    try:
      await context.bot.send_message(
          chat_id=hedef_user_id, text=VIP_LINKLER, parse_mode="Markdown"
      )
      await query.edit_message_text(
          text="✅ Ödeme onaylandı ve linkler müşteriye başarıyla iletildi!"
      )
    except Exception as e:
      await query.edit_message_text(text=f"❌ Gönderim başarısız oldu: {e}")


def main():
  application = ApplicationBuilder().token(TOKEN).build()

  application.add_handler(CommandHandler("start", start))
  application.add_handler(
      MessageHandler(filters.PHOTO | filters.Document.ALL, foto_veya_belge_geldi)
  )
  application.add_handler(CallbackQueryHandler(button_handler))

  print("Bot başarıyla başlatıldı ve çalışıyor...")
  application.run_polling()


if __name__ == "__main__":
  main()
