import os
from dotenv import load_dotenv
from fredapi import Fred

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
fred = Fred(api_key=FRED_API_KEY)

def predict(ticker: str, horizon: str = "day") -> dict:
    print(f"[trainer_5_macro] Checking macroeconomic indicators for {ticker}...")

    try:
        # Fetch most recent data
        cpi_data = fred.get_series_latest_release("CPIAUCSL")       # Consumer Price Index
        fed_data = fred.get_series_latest_release("FEDFUNDS")       # Federal Funds Rate
        unemp_data = fred.get_series_latest_release("UNRATE")       # Unemployment Rate

        cpi = float(cpi_data.iloc[-1])
        fed_rate = float(fed_data.iloc[-1])
        unemp = float(unemp_data.iloc[-1])


        # Score calculation
        prediction = 0.0
        confidence = 0.3
        reasons = []

        # CPI logic
        if cpi < 300:
            prediction += 0.01
            reasons.append("Moderate inflation (CPI)")
        else:
            prediction -= 0.01
            reasons.append("High inflation (CPI)")

        # Interest rate logic
        if fed_rate < 3.0:
            prediction += 0.02
            reasons.append("Low Fed interest rate")
        elif fed_rate > 5.0:
            prediction -= 0.02
            reasons.append("High Fed interest rate")

        # Unemployment logic
        if unemp < 4.0:
            prediction += 0.01
            reasons.append("Strong job market")
        else:
            prediction -= 0.01
            reasons.append("Elevated unemployment")

        # Set confidence higher if all metrics were successfully pulled
        confidence = 0.9

        return {
            "trainer": "macro",
            "prediction": round(prediction, 5),
            "adjustment": 1.0 + round(prediction, 5),
            "confidence": confidence,
            "meta": {
                "cpi": cpi,
                "fed_rate": fed_rate,
                "unemployment_rate": unemp,
                "reason": ", ".join(reasons)
            }
        }

    except Exception as e:
        return {
            "trainer": "macro",
            "prediction": 0.0,
            "adjustment": 1.0,
            "confidence": 0.0,
            "meta": {
                "error": str(e),
                "reason": "Failed to retrieve macroeconomic indicators"
            }
        }
