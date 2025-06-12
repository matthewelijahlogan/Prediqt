# trainer_6_earnings.py

import yfinance as yf

def predict(ticker: str):
    print(f"[trainer_6_earnings] Evaluating earnings report impact for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        cal = stock.calendar

        print(f"[earnings_model] Calendar type: {type(cal)}")

        if hasattr(cal, "empty") and cal.empty:
            print("[earnings_model] No earnings calendar available.")
            return {"adjustment": 1.0, "earnings_result": "unknown"}

        # If calendar is dict (sometimes returned as dict?), handle gracefully
        if isinstance(cal, dict):
            print("[earnings_model] Calendar is a dict, unable to process earnings date properly.")
            return {"adjustment": 1.0, "earnings_result": "unknown"}

        eps_actual = stock.info.get("epsActual")
        eps_estimate = stock.info.get("epsEstimate")

        if eps_actual is None or eps_estimate is None:
            print("[earnings_model] EPS data unavailable.")
            return {"adjustment": 1.0, "earnings_result": "unknown"}

        # Determine the result
        if eps_actual > eps_estimate:
            result = "beat"
            adjustment = 1.05
        elif eps_actual < eps_estimate:
            result = "miss"
            adjustment = 0.95
        else:
            result = "meet"
            adjustment = 1.0

        output = {
            "adjustment": round(adjustment, 3),
            "earnings_result": result,
            "eps_actual": eps_actual,
            "eps_estimate": eps_estimate,
        }

        print(f"[earnings_model] Output: {output}")
        return output

    except Exception as e:
        print(f"[earnings_model] Error: {e}")
        return {"adjustment": 1.0, "earnings_result": "error"}
