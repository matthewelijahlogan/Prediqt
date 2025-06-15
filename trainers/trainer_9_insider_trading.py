import yfinance as yf
import pandas as pd

def predict(ticker: str):
    print(f"[trainer_9_insider_trading] Checking insider trading activity for {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        insider_trades = getattr(stock, 'insider_transactions', None)

        if insider_trades is None or insider_trades.empty:
            print("[insider_model] No insider transactions found, returning neutral adjustment.")
            return {
                "adjustment": 1.0,
                "insider_activity": "none",
                "reasoning": "No insider trades"
            }

        # Normalize columns (strip whitespace)
        insider_trades.columns = [col.strip() for col in insider_trades.columns]

        # Handle alternative column names by renaming
        if 'Date' not in insider_trades.columns and 'Start Date' in insider_trades.columns:
            insider_trades.rename(columns={'Start Date': 'Date'}, inplace=True)

        if 'Transaction Type' not in insider_trades.columns and 'Transaction' in insider_trades.columns:
            insider_trades.rename(columns={'Transaction': 'Transaction Type'}, inplace=True)

        # Re-check required columns
        if 'Date' not in insider_trades.columns or 'Transaction Type' not in insider_trades.columns:
            print(f"[insider_model] Required columns missing. Columns found: {insider_trades.columns}")
            return {
                "adjustment": 1.0,
                "insider_activity": "error",
                "reasoning": "Required columns ('Date', 'Transaction Type') missing"
            }

        # Convert date
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
            adjustment = 1.05
            activity = "buy"
            reasoning = f"More insider buys ({buy_count}) than sells ({sell_count}) in last 30 days"
        elif sell_count > buy_count:
            adjustment = 0.95
            activity = "sell"
            reasoning = f"More insider sells ({sell_count}) than buys ({buy_count}) in last 30 days"
        else:
            adjustment = 1.0
            activity = "neutral"
            reasoning = f"Insider buys and sells balanced ({buy_count} each) in last 30 days"

        result = {
            "adjustment": adjustment,
            "insider_activity": activity,
            "reasoning": reasoning,
        }

        print(f"[insider_model] Output: {result}")
        return result

    except Exception as e:
        print(f"[insider_model] Error: {e}")
        return {
            "adjustment": 1.0,
            "insider_activity": "error",
            "reasoning": str(e)
        }
