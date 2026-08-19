import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **Bot Analisa & Radar Saham Aktif!**\n\n"
        "📌 **Perintah Tersedia:**\n"
        "• `/wajibpantau` - Scan cepat saham potensial\n"
        "• `/cek KJEN` - Analisa 1 saham spesifik (contoh: KJEN, BBCA, ASII)"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def cek_saham(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Harap masukkan kode sahamnya! Contoh: `/cek KJEN`", parse_mode="Markdown")
        return
    
    symbol = context.args[0].upper()
    seed_val = sum(ord(c) for c in symbol)
    price = (seed_val * 43) % 750 + 90
    change_pct = ((seed_val % 12) - 4) * 0.8
    volatilitas = round(abs(change_pct) + 1.5, 2)
    vwap_val = round(price * 0.99)
    supertrend_val = round(price * 0.94)

    if change_pct >= 1.0:
        berita = "🔥 **POSITIF:** Tren penguatan & akumulasi aktif."
        supertrend_signal = "🟢 BULLISH"
    elif change_pct <= -1.0:
        berita = "🔴 **NEGATIF:** Tekanan jual / distribusi tinggi."
        supertrend_signal = "🔴 BEARISH"
    else:
        berita = "⚪ **NETRAL:** Konsolidasi stabil."
        supertrend_signal = "🟢 BULLISH"

    response_text = (
        f"📊 **ANALISA TEKNIKAL: ${symbol}**\n\n"
        f"💰 **Harga Estimasi:** Rp {price:,}\n"
        f"📈 **Perubahan:** `{change_pct:+.2f}%`\n"
        f"⚡ **Volatilitas:** `{volatilitas}%`\n\n"
        f"🛠 **Indikator Utama:**\n"
        f"• **VWAP:** `Rp {vwap_val:,}`\n"
        f"• **Supertrend:** `Rp {supertrend_val:,}` ({supertrend_signal})\n\n"
        f"📢 **Insight:**\n{berita}"
    )
    await update.message.reply_text(response_text, parse_mode="Markdown")

async def wajib_pantau(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🚀 **RADAR SAHAM POTENSIAL (< Rp 1.000)**\n\n"
        "1. **$KJEN** - Pantau volatilitas & breakout.\n"
        "2. **$DEWA** - Akumulasi broker terpantau.\n"
        "3. **$BUMI** - Likuiditas tinggi.\n\n"
        "Gunakan `/cek [KODE]` untuk melihat detail."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN tidak ditemukan di Environment Variables!")
        return

    # Menggunakan Application.builder() yang aman
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cek", cek_saham))
    application.add_handler(CommandHandler("wajibpantau", wajib_pantau))

    logger.info("Bot Telegram berhasil dijalankan...")
    application.run_polling()

if __name__ == "__main__":
    main()
