import yfinance as yf
import pandas as pd
import numpy as np

def predict(ticker: str):
    print(f"[trainer_11_technical_indicators] Evaluating technical indicators for {ticker}...")

    try:
        df = yf.download(ticker, period="1mo", interval="1h", progress=False)

        if df.empty or len(df) < 30:
            print("[trainer_11] Not enough data.")
            return {"adjustment": 1.0, "reason": "insufficient_data"}

        # Close price reference
        close = df["Close"]
        price = close.iloc[-1]

        ### RSI
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-6)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        ### MACD
        ema_fast = close.ewm(span=12, adjust=False).mean()
        ema_slow = close.ewm(span=26, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - signal

        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_hist = macd_hist.iloc[-1]

        ### Bollinger Bands
        bb_mid = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        upper_band = bb_mid + 2 * bb_std
        lower_band = bb_mid - 2 * bb_std

        upper = upper_band.iloc[-1]
        lower = lower_band.iloc[-1]

        ### Scoring with explicit float casts for safety
        rsi_score = 0
        try:
            rsi_val = float(current_rsi)
            if rsi_val < 30:
                rsi_score = 1
            elif rsi_val > 70:
                rsi_score = -1
        except Exception as e:
            print(f"[trainer_11] RSI score error: {e}")

        macd_score = 0
        try:
            macd_val = float(current_macd)
            signal_val = float(current_signal)
            if macd_val > signal_val:
                macd_score = 1
            elif macd_val < signal_val:
                macd_score = -1
        except Exception as e:
            print(f"[trainer_11] MACD score error: {e}")

        bb_score = 0
        try:
            price_val = float(price)
            lower_val = float(lower)
            upper_val = float(upper)
            if price_val < lower_val:
                bb_score = 1
            elif price_val > upper_val:
                bb_score = -1
        except Exception as e:
            print(f"[trainer_11] Bollinger Bands score error: {e}")

        total_score = rsi_score + macd_score + bb_score
        adjustment = 1.0 + (total_score * 0.02)  # Max swing of ±6%

        output = {
            "adjustment": round(adjustment, 3),
            "rsi": round(float(current_rsi), 2),
            "macd": round(float(current_macd), 4),
            "macd_signal": round(float(current_signal), 4),
            "macd_histogram": round(float(current_hist), 4),
            "bollinger_upper": round(float(upper), 2),
            "bollinger_lower": round(float(lower), 2),
            "price": round(float(price), 2),
            "rsi_score": rsi_score,
            "macd_score": macd_score,
            "bollinger_score": bb_score,
            "total_score": total_score
        }

        print(f"[trainer_11] Output: {output}")
        return output

    except Exception as e:
        print(f"[trainer_11] Error: {e}")
        return {"adjustment": 1.0, "error": str(e)}
