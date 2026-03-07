from fastapi import APIRouter, HTTPException, Query
from backend.yfinance_client import get_quote

router = APIRouter()

@router.get("/quote")
def quote(ticker: str = Query(...)):
    try:
        return get_quote(ticker)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
