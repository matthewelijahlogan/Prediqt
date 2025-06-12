import requests
from bs4 import BeautifulSoup

def get_pelosi_trades(ticker: str):
    url = "https://senatestockwatcher.com/summary_by_rep/Nancy%20Pelosi/"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[pelosi_scraper] Failed to get page: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table", {"class": "table"})
    if not table:
        print("[pelosi_scraper] No trades table found.")
        return None

    rows = table.find_all("tr")
    trades = []

    for row in rows[1:]:  # skip the header
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        trade_ticker = cols[0].text.strip().upper()
        if trade_ticker == ticker.upper():
            trades.append({
                "ticker": trade_ticker,
                "date": cols[1].text.strip(),
                "transaction": cols[2].text.strip(),
                "amount": cols[3].text.strip(),
                "owner": cols[4].text.strip()
            })

    if not trades:
        print(f"[pelosi_scraper] No recent trades found for {ticker}.")
        return None

    # Most recent trade first (site usually orders this way)
    return trades[0]
