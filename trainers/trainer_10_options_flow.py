import yfinance as yf

def predict(ticker: str, horizon: str = "day") -> dict:
    print(f"[trainer_10_options_flow] Running options flow analysis for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options

        if not expirations:
            return {
                "trainer": "options_flow",
                "prediction": 0.0,
                "confidence": 0.0,
                "meta": {
                    "reasoning": "No options expirations found"
                }
            }

        # Nearest expiration
        nearest_exp = expirations[0]
        options_chain = stock.option_chain(nearest_exp)

        calls = options_chain.calls
        puts = options_chain.puts

        total_calls_oi = calls['openInterest'].sum()
        total_puts_oi = puts['openInterest'].sum()
        total_calls_volume = calls['volume'].sum()
        total_puts_volume = puts['volume'].sum()

        oi_ratio = total_calls_oi / max(total_puts_oi, 1)
        vol_ratio = total_calls_volume / max(total_puts_volume, 1)

        signal_strength = (oi_ratio + vol_ratio) / 2

        # Calculate delta and confidence
        delta = min(max(signal_strength - 1, -1), 1) * 0.05  # cap delta in [-0.05, +0.05]
        confidence = round(min(1.0, abs(signal_strength - 1)), 3)

        result = {
            "trainer": "options_flow",
            "prediction": round(delta, 5),
            "confidence": confidence,
            "meta": {
                "signal_strength": round(signal_strength, 3),
                "call_oi": int(total_calls_oi),
                "put_oi": int(total_puts_oi),
                "call_vol": int(total_calls_volume),
                "put_vol": int(total_puts_volume),
                "reasoning": f"OI ratio={round(oi_ratio,2)}, Vol ratio={round(vol_ratio,2)}"
            }
        }

        print(f"[options_model] Output: {result}")
        return result

    except Exception as e:
        print(f"[options_model] Error: {e}")
        return {
            "trainer": "options_flow",
            "prediction": 0.0,
            "confidence": 0.0,
            "meta": {
                "reasoning": str(e)
            }
        }

if __name__ == "__main__":
    # Simple tester for a few tickers
    for test_ticker in ["AAPL", "TSLA", "GOOGL"]:
        print(f"\nTesting options_flow trainer for {test_ticker}...")
        result = predict(test_ticker)
        print(result)
