# trainer_5_macro.py

import os
from dotenv import load_dotenv
from fredapi import Fred

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
fred = Fred(api_key=FRED_API_KEY)
print("FRED key loaded?", FRED_API_KEY)


def predict(ticker: str):
    print(f"[trainer_5_macro] Checking macroeconomic indicators for {ticker}...")

    try:
        # Most recent values
        cpi = fred.get_series_latest_release('CPIAUCSL')  # Consumer Price Index
        fed_rate = fred.get_series_latest_release('FEDFUNDS')  # Federal Funds Rate
        unemployment = fred.get_series_latest_release('UNRATE')  # Unemployment Rate

        # Normalize values to make an adjustment score
        cpi_val = float(cpi[-1])
        fed_val = float(fed_rate[-1])
        unemp_val = float(unemployment[-1])

        # Simple weighting logic
        # Lower CPI & Unemployment = bullish; Higher Fed rate = bearish
        adjustment = 1.0
        reasoning = []

        if cpi_val < 300:
            adjustment += 0.01
            reasoning.append("CPI moderate")
        else:
            adjustment -= 0.01
            reasoning.append("CPI high")

        if fed_val < 3.0:
            adjustment += 0.02
            reasoning.append("Low interest rates")
        elif fed_val > 5.0:
            adjustment -= 0.02
            reasoning.append("High interest rates")

        if unemp_val < 4.0:
            adjustment += 0.01
            reasoning.append("Strong job market")
        else:
            adjustment -= 0.01
            reasoning.append("Weaker job market")

        result = {
            "adjustment": round(adjustment, 3),
            "cpi": cpi_val,
            "fed_rate": fed_val,
            "unemployment_rate": unemp_val,
            "reasoning": ", ".join(reasoning)
        }

        print(f"[macro_model] Output: {result}")
        return result

    except Exception as e:
        print(f"[macro_model] Error: {e}")
        return {"adjustment": 1.0, "reasoning": "error"}
