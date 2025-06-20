import yfinance as yf
import pandas as pd

def predict(ticker: str, horizon: str = "day") -> dict:
    print(f"[trainer_9_insider_trading] Checking insider trading activity for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        insider_trades = getattr(stock, 'insider_transactions', None)

        if insider_trades is None or insider_trades.empty:
            return {
                "trainer": "insider_trading",
                "prediction": 0.0,
                "confidence": 0.5,
                "meta": {
                    "insider_activity": "none",
                    "reasoning": "No insider trades data available, defaulting to neutral"
                }
            }

        # Normalize and rename columns if necessary
        insider_trades.columns = [col.strip() for col in insider_trades.columns]
        if 'Date' not in insider_trades.columns and 'Start Date' in insider_trades.columns:
            insider_trades.rename(columns={'Start Date': 'Date'}, inplace=True)
        if 'Transaction Type' not in insider_trades.columns and 'Transaction' in insider_trades.columns:
            insider_trades.rename(columns={'Transaction': 'Transaction Type'}, inplace=True)

        if 'Date' not in insider_trades.columns or 'Transaction Type' not in insider_trades.columns:
            return {
                "trainer": "insider_trading",
                "prediction": 0.0,
                "confidence": 0.5,
                "meta": {
                    "insider_activity": "error",
                    "reasoning": "Missing required columns, defaulting to neutral"
                }
            }

        # Convert and filter by date
        insider_trades['Date'] = pd.to_datetime(insider_trades['Date'], errors='coerce')
        recent_trades = insider_trades[
            insider_trades['Date'] >= (pd.Timestamp.today() - pd.Timedelta(days=30))
        ]

        buys = recent_trades[
            recent_trades['Transaction Type'].str.contains("Buy", case=False, na=False)
        ]
        sells = recent_trades[
            recent_trades['Transaction Type'].str.contains("Sell", case=False, na=False)
        ]

        buy_count = len(buys)
        sell_count = len(sells)

        if buy_count > sell_count:
            delta = 0.05
            activity = "buy"
            reasoning = f"{buy_count} insider buys vs {sell_count} sells (last 30 days)"
        elif sell_count > buy_count:
            delta = -0.05
            activity = "sell"
            reasoning = f"{sell_count} insider sells vs {buy_count} buys (last 30 days)"
        else:
            delta = 0.0
            activity = "neutral"
            reasoning = f"{buy_count} buys and {sell_count} sells — balanced activity"

        total_trades = buy_count + sell_count
        if total_trades == 0:
            confidence = 0.5
        else:
            confidence = min(1.0, total_trades / 10.0)

        result = {
            "trainer": "insider_trading",
            "prediction": round(delta, 5),
            "confidence": round(confidence, 3),
            "meta": {
                "insider_activity": activity,
                "buy_count": buy_count,
                "sell_count": sell_count,
                "reasoning": reasoning
            }
        }

        print(f"[insider_model] Output: {result}")
        return result

    except Exception as e:
        print(f"[insider_model] Error: {e}")
        return {
            "trainer": "insider_trading",
            "prediction": 0.0,
            "confidence": 0.5,
            "meta": {
                "insider_activity": "error",
                "reasoning": str(e)
            }
        }

if __name__ == "__main__":
    print(predict("AAPL"))
