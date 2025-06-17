# file: kingmaker/trainer_5_options_pressure.py

import yfinance as yf

def run_model(ticker: str):
    print(f"[Kingmaker: OptionsPressure] ⚖️ Analyzing options data for {ticker}")
    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options

        if not expirations:
            return {
                "score": 0,
                "details": {
                    "model": "OptionsPressure",
                    "note": "No options expiration dates available"
                }
            }

        nearest_exp = expirations[0]
        opt_chain = stock.option_chain(nearest_exp)
        calls = opt_chain.calls
        puts = opt_chain.puts

        call_volume = calls["volume"].sum()
        put_volume = puts["volume"].sum()
        call_oi = calls["openInterest"].sum()
        put_oi = puts["openInterest"].sum()

        epsilon = 1e-6
        volume_ratio = call_volume / (put_volume + epsilon)
        oi_ratio = call_oi / (put_oi + epsilon)

        def ratio_to_score(ratio):
            if ratio < 0.5:
                return 0.0
            elif ratio > 2.0:
                return 1.0
            else:
                return (ratio - 0.5) / 1.5

        volume_score = ratio_to_score(volume_ratio)
        oi_score = ratio_to_score(oi_ratio)
        combined_score = 0.6 * volume_score + 0.4 * oi_score

        return {
            "score": round(combined_score, 4),
            "details": {
                "model": "OptionsPressure",
                "expiration": nearest_exp,
                "volume_ratio": round(volume_ratio, 3),
                "open_interest_ratio": round(oi_ratio, 3),
                "call_volume": int(call_volume),
                "put_volume": int(put_volume),
                "call_open_interest": int(call_oi),
                "put_open_interest": int(put_oi),
            }
        }

    except Exception as e:
        return {
            "score": 0,
            "error": f"OptionsPressure error: {str(e)}"
        }

# Required fusion interface
def get_signal(ticker: str):
    return run_model(ticker)

if __name__ == "__main__":
    print(get_signal("AAPL"))
