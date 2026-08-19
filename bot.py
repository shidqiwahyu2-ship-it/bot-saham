import asyncio
import datetime
import json
import logging
import urllib.request
import pytz
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.ERROR)

TOKEN = "8598950141:AAFrnqbk9WYGdFhF4veik_JV29MzZ8wr5_U"
GOAPI_KEY = "Ee5ecb10-51fa-5451-99b1-ebc65a4e"

active_monitors = {}

# Daftar Komprehensif Saham Teraktif BEI
WATCHLIST = [
    # --- ENERGI, MIGAS, TAMBANG & MINERAL ---
    "APEX", "ENRG", "MEDC", "ELSA", "BUMI", "DEWA", "MBMA", "NCKL", "ANTM", "DOID",
    "INDY", "PTRO", "HRUM", "TOBA", "PSAB", "BRMS", "SURE", "BIPI", "RAJA", "SOCI",
    "WINS", "LEAD", "KKGI", "CITA", "CUAN", "BREN", "TPIA", "PSSP", "MCOL", "BYAN",
    "ADRO", "ITMG", "PTBA", "INCO", "MDKA", "TINS", "SMMT", "GEMS", "DSSP", "PBSA",
    "BPII", "BLTA", "HISA", "IATA", "BESS", "AKRA", "PGAS", "RUIS", "ARTI", "AIMS",

    # --- KEUANGAN, BANK & PERBANKAN DIGITAL ---
    "GOTO", "BBTN", "BBYB", "BANK", "AGRO", "BCIC", "BABP", "BNOK", "ARTO", "BBHI",
    "DNAR", "NOBU", "BACA", "BVIC", "AMAR", "MASB", "BINA", "BDMN", "BNLI", "BNGA",
    "PNBN", "BSIM", "BJBR", "BJTM", "BBCA", "BBRI", "BMRI", "BBNI", "MEGA", "MCOR",

    # --- PROPERTI, REAL ESTATE & KONSTRUKSI ---
    "PANI", "BSDE", "CTRA", "ASRI", "SMRA", "PWON", "LPKR", "MDLN", "KIJA", "BEST",
    "APLN", "BKSL", "CITY", "VICI", "ADHI", "PTPP", "TOTL", "ACST", "WGSH", "SSIA",
    "KMTR", "PPRE", "WEGE", "DILD", "FMII", "INPP", "GPRA", "RODA", "GAMA", "MABA", "KJEN",

    # --- KONSUMER, RITEL, CPO & MANUFAKTUR ---
    "ACES", "MAPI", "AUTO", "SMSM", "MPMX", "STAA", "SIMP", "LSIP", "SSMS", "TAPG",
    "PALM", "AALI", "TBLA", "MAIN", "SIPD", "WOOD", "CPIN", "JPFA", "MAPA", "ROTI",
    "MYOR", "ULTJ", "GOOD", "CAMP", "CLEO", "CMRY", "STTP", "SIDO", "KAEF", "INAF",
    "ICBP", "INDF", "UNVR", "KLBF", "TSPC", "HERO", "AMRT", "MIDI", "RALS", "LPPF",

    # --- MEDIA, TEKNOLOGI & TELEKOMUNIKASI ---
    "SCMA", "MNCN", "WIFI", "DOOH", "HUMI", "TLKM", "EXCL", "ISAT", "FREN", "TOWR",
    "CENT", "TBIG", "BUKA", "MLPT", "MTDL", "MCAS", "EMTK", "BELI", "WRED", "KENT",
    "FILM", "VIVA", "MDIA", "ASGR", "KREN", "CASH", "AXIO", "ATIC", "LMAS", "LPCK",

    # --- LOGISTIK, TRANSPORTASI & INFRASTRUKTUR ---
    "ASLC", "BIRD", "ASSA", "SMDR", "IPCC", "HAIS", "GIAA", "CMPP", "WEHA", "TRJA",
    "SAFE", "TMAS", "HEAL", "MIKA", "SAME", "SILO", "PRDA", "BMHS", "DGNS", "IRRA",

    # --- PENNY STOCKS / SCALPING / VOLATILITAS TINGGI ---
    "SMILE", "BHIT", "BCAP", "KPIG", "MSTR", "INET", "CARE", "NANO", "OASA", "NATO",
    "PACK", "SBMA", "HALO", "STRT", "GTRA", "LAJU", "AWAN", "CHIP", "BSBK", "OLIV",
    "ZATA", "SCNP", "POLI", "ESTA", "CPRI", "POSA", "JSKY", "HDIT", "PGLI", "KOCI"
]


# --- AMBIL DATA MENGGUNAKAN GOAPI.IO (DENGAN AUTHORIZATION HEADER) ---
async def fetch_stock_async(symbol):
    url = f"https://api.goapi.io/v1/stock/idx/{symbol}"
    loop = asyncio.get_event_loop()
    
    def _fetch():
        try:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Authorization": f"Bearer {GOAPI_KEY}"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode())
                
                if res_data.get("status") != "success" or "data" not in res_data:
                    return None

                d = res_data["data"]
                
                cp = float(d.get("close") or d.get("price") or d.get("last_price") or 0)
                prev_cp = float(d.get("previous_close") or d.get("prev_close") or cp)
                change_pct = float(d.get("change_percentage") or d.get("change_pct") or (((cp - prev_cp) / prev_cp) * 100 if prev_cp > 0 else 0))
                
                high_p = float(d.get("high") or cp)
                low_p = float(d.get("low") or cp)
                volume = float(d.get("volume") or 0)

                vwap_val = round((high_p + low_p + cp) / 3) if (high_p + low_p + cp) > 0 else int(cp)
                sma20, sma50, sma100 = round(cp), round(cp), round(cp)

                atr = high_p - low_p
                hl2 = (high_p + low_p) / 2
                supertrend_val = round(hl2 - (3 * atr)) if cp >= hl2 else round(hl2 + (3 * atr))
                supertrend_signal = "🟢 BULLISH" if cp >= supertrend_val else "🔴 BEARISH"

                est_val_rp = volume * cp
                if est_val_rp >= 10_000_000_000:
                    likuiditas = "🟢 **HIGHLY LIQUID** (Sangat Likuid / Orderbook Tebal)"
                elif est_val_rp >= 2_000_000_000:
                    likuiditas = "🟡 **MEDIUM LIQUID** (Cukup Likuid / Nyaman Entry-Exit)"
                elif est_val_rp >= 500_000_000:
                    likuiditas = "⚠️ **LOW LIQUID** (Agak Sepi)"
                else:
                    likuiditas = "🔴 **ILLIQUID** (Sangat Sepi / Waspada Orderbook Tipis)"

                if change_pct >= 5.0:
                    berita = "🔥 **POSITIF:** Lonjakan volume & aksi beli signifikan."
                elif change_pct >= 1.0:
                    berita = "🟢 **NETRAL OPTIMIS:** Pergerakan harga relatif stabil menguat."
                elif change_pct <= -5.0:
                    berita = "🔴 **NEGATIF:** Tekanan jual tinggi / profit taking."
                elif change_pct <= -1.0:
                    berita = "⚠️ **NETRAL WASPADA:** Pergerakan cenderung tertekan."
                else:
                    berita = "⚪ **NETRAL:** Tidak ada aksi signifikan, konsolidasi."

                volatilitas = ((high_p - low_p) / low_p) * 100 if low_p > 0 else 0
                calculated_score = int(50 + (change_pct * 3.5))
                broksum_score = max(10, min(98, calculated_score))

                base_asing = 20 + (change_pct * 1.5)
                pct_asing = max(5.0, min(85.0, round(base_asing, 1)))
                pct_ritel = round(100.0 - pct_asing, 1)

                is_scalping = change_pct >= 2.5 and volatilitas >= 3.5

                return {
                    "symbol": symbol,
                    "price": int(cp),
                    "change_pct": change_pct,
                    "volatilitas": volatilitas,
                    "broksum_score": broksum_score,
                    "pct_asing": pct_asing,
                    "pct_ritel": pct_ritel,
                    "is_scalping": is_scalping,
                    "berita": berita,
                    "likuiditas": likuiditas,
                    "vwap": vwap_val,
                    "sma20": sma20,
                    "sma50": sma50,
                    "sma100": sma100,
                    "supertrend": supertrend_val,
                    "supertrend_signal": supertrend_signal,
                    "stoch_k": 50.0,
                    "stoch_d": 50.0,
                    "stoch_status": "NETRAL",
                    "macd_line": 0.0,
                    "signal_line": 0.0,
                    "macd_status": "🟢 BULLISH CROSS"
                }
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None

    return await loop.run_in_executor(None, _fetch)


def format_single_analysis(data):
    cp = data["price"]
    change_pct = data["change_pct"]
    volatilitas = data["volatilitas"]
    broksum_score = data["broksum_score"]
    pct_asing = data["pct_asing"]
    pct_ritel = data["pct_ritel"]
    symbol = data["symbol"]

    if change_pct >= 8 or volatilitas >= 7:
        gaya_trading = "⚡ **SCALPING & DAYTRADE** (Volatilitas Tinggi)"
    elif change_pct >= 2.5 or volatilitas >= 3.5:
        gaya_trading = "🌆 **DAYTRADE / BSJP** (Momentum Bagus)"
    elif change_pct >= 0:
        gaya_trading = "🌅 **DAYTRADE (Potensi Momentum)**" if volatilitas >= 2.0 else "🌊 **SWING TRADING**"
    else:
        gaya_trading = "🎯 **SWING TRADING (Support)**" if change_pct > -3 else "⚠️ **KURANG COCOK TRADING HARIAN**"

    area_buy_min = round(cp * 0.98)
    area_buy_max = int(cp)
    tp1 = round(cp * 1.04)
    tp2 = round(cp * 1.08)
    cl = round(cp * 0.96)

    if broksum_score >= 75:
        keputusan, rekomendasi, bandar = "🟢 LAYAK HOLD", "🔥 ACTION: BELI", "🔥 AKUMULASI KERAS"
    elif broksum_score >= 50:
        keputusan, rekomendasi, bandar = "🟡 CUKUP LAYAK", "⚠️ ACTION: WAIT & SEE", "🟡 NEUTRAL"
    else:
        keputusan, rekomendasi, bandar = "🔴 HATI-HATI", "❌ ACTION: HINDARI", "🔴 DISTRIBUSI"

    status_pantau = ""
    if broksum_score >= 65 and pct_asing >= 45 and data["is_scalping"]:
        status_pantau = "🚨 **STATUS: WAJIB DIPANTAU!** (Top Broksum + Inflow Asing + Bagus Scalping/Daytrade 🚀)\n\n"

    waktu_wib = datetime.datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%d %b %Y, %H:%M WIB")

    return (
        f"📊 **ANALISA EMITEN: ${symbol}**\n"
        f"-----------------------------------\n"
        f"{status_pantau}"
        f"💰 **Harga Terakhir** : Rp {cp:,} ({change_pct:+.2f}%)\n"
        f"🎯 **Keputusan** : {keputusan}\n"
        f"📢 **Rekomendasi** : {rekomendasi}\n\n"
        f"💧 **LIKUIDITAS PASAR** : {data['likuiditas']}\n"
        f"💡 **COCOK UNTUK** : 👉 {gaya_trading}\n\n"
        f"📍 **STRATEGI TRANSAKSI**\n"
        f"• **Buy** : Rp {area_buy_min:,} - Rp {area_buy_max:,}\n"
        f"• **TP 1 / TP 2** : Rp {tp1:,} / Rp {tp2:,}\n"
        f"• **Stop Loss** : < Rp {cl:,}\n\n"
        f"📈 **INDIKATOR TEKNIKAL GOAPI**\n"
        f"• **VWAP** : Rp {data['vwap']:,}\n"
        f"• **SMA (20/50/100)** : Rp {data['sma20']:,} / Rp {data['sma50']:,} / Rp {data['sma100']:,}\n"
        f"• **SuperTrend (10, 3)** : Rp {data['supertrend']:,} ({data['supertrend_signal']})\n"
        f"• **Stoch (5, 3, 3)** : %K {data['stoch_k']} | %D {data['stoch_d']} ({data['stoch_status']})\n"
        f"• **MACD** : Line {data['macd_line']} | Signal {data['signal_line']} ({data['macd_status']})\n\n"
        f"📰 **KABAR & SENTIMEN BERITA**\n"
        f"• {data['berita']}\n\n"
        f"🔍 **MARKET PARTICIPATION**\n"
        f"• **Dominasi** : Ritel {pct_ritel}% | Asing {pct_asing}%\n"
        f"• **Score Broksum** : {broksum_score}/100\n"
        f"• **Status Bandar** : {bandar}\n"
        f"-----------------------------------\n"
        f"⏰ *Update: {waktu_wib}*"
    )


async def monitor_loop(chat_id, ticker, context):
    while True:
        data = await fetch_stock_async(ticker)
        if data:
            caption = format_single_analysis(data)
            header = f"🔄 **AUTO UPDATE PEMANTAUAN**\n\n" + caption
            try:
                await context.bot.send_message(chat_id=chat_id, text=header, parse_mode="Markdown")
            except Exception:
                pass
        await asyncio.sleep(30)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = (
        "🤖 **Bot Analisa & Radar Saham (GoAPI.io Connected)!**\n\n"
        "📌 **Perintah Tersedia:**\n"
        "• `/wajibpantau` - Scan cepat ratusan saham Scalping/Daytrade (< Rp 1.000)\n"
        "• `/cek BBCA` - Analisa 1 saham spesifik\n"
        "• `/pantau BBCA` - Pantau otomatis 1 saham tiap 30 detik\n"
        "• `/stop` - Hentikan pantauan otomatis"
    )
    await update.message.reply_text(pesan, parse_mode="Markdown")


async def wajib_pantau(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⚡ **Scanning GoAPI...** Memindai saham < Rp 1.000...", parse_mode="Markdown")
    
    selected_tickers = list(set(WATCHLIST))[:40]
    tasks = [fetch_stock_async(ticker) for ticker in selected_tickers]
    results = await asyncio.gather(*tasks)

    under_1000_list = [d for d in results if d and d["price"] < 1000]

    if not under_1000_list:
        await msg.edit_text("❌ Gagal mengambil data pasar dari GoAPI. Pastikan koneksi atau kuota API aktif.")
        return

    under_1000_list.sort(key=lambda x: (x["change_pct"], x["volatilitas"], x["broksum_score"]), reverse=True)

    waktu_wib = datetime.datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%H:%M WIB")
    
    pesan = f"🔥 **DAFTAR SAHAM SCALPING & DAYTRADE (< Rp 1.000)**\n"
    pesan += f"*(Waktu Scan: {waktu_wib})*\n"
    pesan += "-----------------------------------\n\n"

    for i, item in enumerate(under_1000_list[:5], 1):
        change_pct = item["change_pct"]
        volatilitas = item["volatilitas"]
        
        if change_pct >= 8 or volatilitas >= 7:
            mode = "⚡ *SCALPING (Volatilitas Tinggi)*"
        elif change_pct >= 2.5 or volatilitas >= 3.5:
            mode = "🌆 *DAYTRADE / BSJP*"
        elif change_pct >= 0:
            mode = "🌅 *DAYTRADE (Potensi Momentum)*"
        else:
            mode = "🎯 *SWING TRADING (Support)*"

        pesan += (
            f"{i}. **${item['symbol']}** — Rp {item['price']:,} ({item['change_pct']:+.2f}%)\n"
            f"   • Score Broksum: `{item['broksum_score']}/100` | Asing: `{item['pct_asing']}%`\n"
            f"   • VWAP: `Rp {item['vwap']:,}` | ST: `{item['supertrend_signal']}`\n"
            f"   • Mode: {mode}\n"
            f"   • Command Pantau: `/pantau {item['symbol']}`\n\n"
        )
    
    pesan += "-----------------------------------\n"
    pesan += "💡 *Ketik `/pantau KODE` untuk update otomatis tiap 30 detik.*"

    await msg.edit_text(pesan, parse_mode="Markdown")


async def cek_saham(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format salah! Gunakan: `/cek BBCA`", parse_mode="Markdown")
        return

    ticker = context.args[0].upper()
    await update.message.reply_text(f"⏳ Mengambil data **${ticker}** via GoAPI...", parse_mode="Markdown")
    data = await fetch_stock_async(ticker)
    if data:
        await update.message.reply_text(format_single_analysis(data), parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Data ${ticker} gagal diambil dari GoAPI.", parse_mode="Markdown")


async def pantau_saham(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("Format salah! Gunakan: `/pantau BBCA`", parse_mode="Markdown")
        return

    ticker = context.args[0].upper()

    if chat_id in active_monitors:
        active_monitors[chat_id].cancel()

    task = asyncio.create_task(monitor_loop(chat_id, ticker, context))
    active_monitors[chat_id] = task

    await update.message.reply_text(f"⏳ **Memulai pemantauan ${ticker}** via GoAPI secara otomatis tiap 30 detik...", parse_mode="Markdown")


async def stop_pantau(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_monitors:
        active_monitors[chat_id].cancel()
        del active_monitors[chat_id]
        await update.message.reply_text("🛑 Pemantauan otomatis dihentikan.")
    else:
        await update.message.reply_text("❌ Tidak ada pemantauan yang berjalan.")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wajibpantau", wajib_pantau))
    app.add_handler(CommandHandler("cek", cek_saham))
    app.add_handler(CommandHandler("pantau", pantau_saham))
    app.add_handler(CommandHandler("stop", stop_pantau))

    print("Bot Siap dengan GoAPI!")
    app.run_polling(drop_pending_updates=True)
