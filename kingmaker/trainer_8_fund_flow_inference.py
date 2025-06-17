# file: kingmaker/trainer_8_fund_flow_inference.py

import yfinance as yf

def run_model(ticker: str):
    print(f"[Kingmaker: FundFlowInference] 🧠 Analyzing institutional fund flow for {ticker}")

    try:
        stock = yf.Ticker(ticker)

        holders = stock.institutional_holders
        if holders is None or holders.empty:
            return {
                "score": 0.5,
                "details": {
                    "model": "FundFlowInference",
                    "note": "No institutional holder data available"
                }
            }

        # Heuristic: Compare shares held vs % change
        positive_moves = 0
        negative_moves = 0
        neutral_moves = 0
        total = 0

        for _, row in holders.iterrows():
            change = row.get("Change", 0)
            if change > 0:
                positive_moves += 1
            elif change < 0:
                negative_moves += 1
            else:
                neutral_moves += 1
            total += 1

        if total == 0:
            score = 0.5  # no signal
        else:
            score = (positive_moves - negative_moves) / total
            score = (score + 1) / 2  # normalize to 0–1

        return {
            "score": round(score, 4),
            "details": {
                "model": "FundFlowInference",
                "positive_holders": positive_moves,
                "negative_holders": negative_moves,
                "neutral_holders": neutral_moves,
                "total_holders": total
            }
        }

    except Exception as e:
        return {
            "score": 0,
            "error": f"Fund flow analysis error: {str(e)}"
        }


# Required fusion interface
def get_signal(ticker: str):
    return run_model(ticker)


if __name__ == "__main__":
    print(get_signal("AAPL"))
