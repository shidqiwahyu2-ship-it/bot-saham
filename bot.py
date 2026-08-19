async def fetch_stock_async(symbol):
    # Perbaikan URL endpoint resmi GoAPI untuk mengambil harga/data saham
    url = f"https://api.goapi.io/v1/stock/idx/price?symbols={symbol}"
    loop = asyncio.get_event_loop()
    
    def _fetch():
        try:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Authorization": GOAPI_KEY  # Sesuai standar dokumentasi GoAPI (tanpa Bearer)
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode())
                
                if res_data.get("status") != "success" or "data" not in res_data:
                    return None

                # Menyesuaikan dengan format balikan data dari endpoint price GoAPI
                data_list = res_data["data"]
                if not data_list:
                    return None
                    
                d = data_list[0] if isinstance(data_list, list) else data_list
                
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
