def _ticker_tape_price(ticker):
    from backend.routers.ticker_tape import TICKER_CACHE

    match = next(
        (item for item in TICKER_CACHE["tickers"] if item.get("symbol") == ticker.upper()),
        None,
    )
    price = match.get("price") if match else None
    return float(price) if isinstance(price, (int, float)) else None


def _single_series(frame, column):
    values = frame[column]
    if getattr(values, "ndim", 1) > 1:
        values = values.iloc[:, 0]
    return values.dropna()


def get_quote(ticker):
    import yfinance as yf

    symbol = ticker.upper()
    price = _ticker_tape_price(symbol)
    previous_close = None
    volume = None

    try:
        history = yf.download(
            symbol,
            period="5d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if not history.empty:
            closes = _single_series(history, "Close")
            volumes = _single_series(history, "Volume")
            if price is None and not closes.empty:
                price = float(closes.iloc[-1])
            if len(closes) >= 2:
                previous_close = float(closes.iloc[-2])
            if not volumes.empty:
                volume = int(volumes.iloc[-1])
    except Exception as error:
        if price is None:
            raise RuntimeError(f"Market quote unavailable for {symbol}: {error}") from error

    if price is None:
        raise RuntimeError(f"Market quote unavailable for {symbol}")

    change = price - previous_close if previous_close is not None else None
    percent_change = (
        change / previous_close * 100
        if change is not None and previous_close
        else None
    )
    return {
        "ticker": symbol,
        "price": round(price, 2),
        "change": round(change, 2) if change is not None else None,
        "percent_change": round(percent_change, 2) if percent_change is not None else None,
        "volume": volume,
        "market_cap": None,
        "sector": None,
        "source": "ticker_tape_cache" if _ticker_tape_price(symbol) is not None else "daily_history",
    }
