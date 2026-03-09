from .pelosi_scraper import get_pelosi_trades

def predict(ticker: str, horizon: str = "day") -> dict:
    print(f"[trainer_3_pelosi] Checking trades for {ticker}...")
    # Scraper does not take a ticker arg; pull recent trades then filter locally.
    trades = get_pelosi_trades(page=1, page_size=100)

    ticker_upper = ticker.upper()
    matched_trades = []
    for t in trades:
        symbol = (
            t.get("ticker")
            or t.get("symbol")
            or (t.get("asset") or {}).get("ticker")
            or (t.get("asset") or {}).get("symbol")
            or ""
        )
        if isinstance(symbol, str) and symbol.upper() == ticker_upper:
            matched_trades.append(t)

    if not matched_trades:
        return {
            "trainer": "pelosi",
            "prediction": 0.0,
            "confidence": 0.0,
            "meta": {"matched": False, "reason": "No recent trades found"}
        }

    total_effect = 0.0
    matched = []
    for t in matched_trades:
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
