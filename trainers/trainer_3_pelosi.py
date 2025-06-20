from .pelosi_scraper import get_pelosi_trades

def predict(ticker: str, horizon: str = "day") -> dict:
    print(f"[trainer_3_pelosi] Checking trades for {ticker}...")
    trades = get_pelosi_trades(ticker, page=1, page_size=50)

    if not trades:
        return {
            "trainer": "pelosi",
            "prediction": 0.0,
            "confidence": 0.0,
            "meta": {"matched": False, "reason": "No recent trades found"}
        }

    total_effect = 0.0
    matched = []
    for t in trades:
        tx = t.get("txType", "").lower()
        effect = 0.05 if tx in {"buy", "purchase"} else -0.05 if tx in {"sell", "sale"} else 0.0
        total_effect += effect
        matched.append({
            "ticker": ticker,
            "transaction": tx,
            "amount": t.get("value"),
            "owner": t.get("politician", {}).get("politician_lastName"),
            "date": t.get("txDate")
        })

    total_effect = max(min(total_effect, 1.0), -1.0)
    confidence = round(min(1.0, abs(total_effect)), 2)

    return {
        "trainer": "pelosi",
        "prediction": round(total_effect, 5),
        "confidence": confidence,
        "meta": {
            "matched": True,
            "num_trades": len(matched),
            "trades": matched
        }
    }
