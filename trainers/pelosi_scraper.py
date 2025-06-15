import requests
from bs4 import BeautifulSoup
import time

def get_pelosi_trades(ticker: str, max_pages: int = 2000, delay: float = 1.0):
    base_url = "https://www.capitoltrades.com/trades"
    
    # Multiple politician IDs (Pelosi + others)
    politicians = [
        "K000389",  # Nancy Pelosi
        "G000599",  # Marjorie Taylor Greene
        "M001157",  # Joe Manchin
        "G000583",  # Matt Gaetz
        "T000278",  # Tommy Tuberville
    ]
    
    for page in range(1, max_pages + 1):
        try:
            response = requests.get(
                base_url,
                params={"politician": politicians, "page": page},
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            print(f"[pelosi_scraper] Failed to fetch page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", {"class": "table"})

        if not table:
            print(f"[pelosi_scraper] No trades table found on page {page}.")
            break

        rows = table.find_all("tr")
        for row in rows[1:]:  # Skip table header
            cols = row.find_all("td")
            if len(cols) < 5:
                continue

            trade_ticker = cols[0].text.strip().upper()
            if trade_ticker == ticker.upper():
                print(f"[pelosi_scraper] Found trade for {ticker} on page {page}")
                return {
                    "ticker": trade_ticker,
                    "date": cols[1].text.strip(),
                    "transaction": cols[2].text.strip(),
                    "amount": cols[3].text.strip(),
                    "owner": cols[4].text.strip()
                }

        print(f"[pelosi_scraper] No match on page {page}. Moving on...")
        time.sleep(delay)  # Be polite to avoid getting blocked

    print(f"[pelosi_scraper] No trades found for {ticker} after checking {max_pages} pages.")
    return None
