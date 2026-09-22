from fastapi import APIRouter, HTTPException, Query

from kingmaker.model import MODEL_VERSION, predict

router = APIRouter(prefix="/api/kingmaker", tags=["kingmaker"])


@router.get("/status")
def status():
    return {"model": MODEL_VERSION, "validation": "purged_expanding_window",
            "execution": "paper", "profitability": "unproven",
            "horizons": ["hour", "day", "week", "month"]}


@router.get("/forecasts")
def forecasts(limit: int = Query(100, ge=1, le=500)):
    from kingmaker.ledger import recent
    return {"items": recent(limit)}


@router.post("/settle")
def settle_forecasts():
    from kingmaker.ledger import settle
    return settle()


@router.get("/scan")
def scan(tickers: str = Query("AAPL,MSFT,NVDA,SPY", max_length=220),
         horizon: str = Query("day", pattern="^(hour|day|week|month)$")):
    symbols = list(dict.fromkeys(s.strip().upper() for s in tickers.split(",") if s.strip()))
    if not 1 <= len(symbols) <= 20:
        raise HTTPException(422, "Provide between 1 and 20 symbols")
    items, errors = [], []
    for symbol in symbols:
        try:
            items.append(predict(symbol, horizon))
        except (ValueError, RuntimeError) as error:
            errors.append({"ticker": symbol, "error": str(error)})
    items.sort(key=lambda item: (item["signal"]["qualified"],
                                item["validation_confidence"],
                                abs(item["signal"]["expected_move_percent"])), reverse=True)
    return {"model": MODEL_VERSION, "items": items, "errors": errors,
            "qualified_count": sum(item["signal"]["qualified"] for item in items)}
