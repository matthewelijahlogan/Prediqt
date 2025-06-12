# trainer_10_options_flow.py

import yfinance as yf
from datetime import datetime, timedelta

def predict(ticker: str):
    print(f"[trainer_10_options_flow] Running options flow analysis for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options
        if not expirations:
            print("[options_model] No options data available.")
            return {"options_signal_strength": 0.0, "options_prediction_confidence": 0.0, "reasoning": "No options expirations"}

        # Pick the nearest expiration date
        nearest_exp = expirations[0]
        options_chain = stock.option_chain(nearest_exp)

        calls = options_chain.calls
        puts = options_chain.puts

        # Calculate total open interest and volume for calls and puts
        total_calls_oi = calls['openInterest'].sum()
        total_puts_oi = puts['openInterest'].sum()
        total_calls_volume = calls['volume'].sum()
        total_puts_volume = puts['volume'].sum()

        # Calculate simple metrics
        oi_ratio = total_calls_oi / max(total_puts_oi, 1)  # Avoid division by zero
        vol_ratio = total_calls_volume / max(total_puts_volume, 1)

        # Simple heuristic for signal strength: calls vs puts dominance
        signal_strength = (oi_ratio + vol_ratio) / 2  # average of OI and volume ratios
        # Normalize to 0..1 scale roughly, capping values > 2 as strong bullish (1), <0.5 strong bearish (0)
        if signal_strength > 2:
            confidence = 1.0
        elif signal_strength < 0.5:
            confidence = 1.0
        else:
            confidence = abs(signal_strength - 1)  # confidence higher as ratio deviates from 1

        # Clamp signal_strength between 0 and 2 for clarity
        signal_strength = min(max(signal_strength, 0), 2)

        result = {
            "options_signal_strength": round(signal_strength, 3),
            "options_prediction_confidence": round(confidence, 3),
            "reasoning": f"Calls OI: {total_calls_oi}, Puts OI: {total_puts_oi}, Calls Vol: {total_calls_volume}, Puts Vol: {total_puts_volume}"
        }

        print(f"[options_model] Output: {result}")
        return result

    except Exception as e:
        print(f"[options_model] Error: {e}")
        return {"options_signal_strength": 0.0, "options_prediction_confidence": 0.0, "reasoning": str(e)}
