from .pelosi_scraper import get_pelosi_trades

def predict(ticker: str):
    print(f"[trainer_3_pelosi] Checking Pelosi trades for {ticker}...")

    trade = get_pelosi_trades(ticker)

    if not trade:
        print(f"[pelosi_model] No relevant Pelosi trades found for {ticker}.")
        return {"adjustment": 1.0, "matched": False}

    transaction = trade['transaction'].lower()
    if "purchase" in transaction or "buy" in transaction:
        adjustment = 1.15
        matched = True
    elif "sale" in transaction or "sell" in transaction:
        adjustment = 0.85
        matched = True
    else:
        adjustment = 1.0
        matched = True

    print(f"[pelosi_model] Output: {{'adjustment': {adjustment}, 'matched': {matched}}}")
    return {"adjustment": adjustment, "matched": matched}
