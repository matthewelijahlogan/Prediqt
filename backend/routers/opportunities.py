"""Bounded background scans keep the terminal responsive during provider work."""
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import re
import time
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from kingmaker.opportunities import DEFAULT_SYMBOLS, build_board

router = APIRouter(prefix="/api/kingmaker/opportunities", tags=["kingmaker"])
_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="kingmaker-desk")
_lock = Lock()
_jobs = {}


class ScanRequest(BaseModel):
    tickers: str = Field(DEFAULT_SYMBOLS, max_length=330)
    horizon: Literal["hour", "day", "week", "month"] = "day"
    cost_bps: float = Field(20, ge=0, le=500, allow_inf_nan=False)


@router.post("")
def start_scan(request: ScanRequest):
    symbols = list(dict.fromkeys(s.strip().upper() for s in request.tickers.split(",") if s.strip()))
    if not 1 <= len(symbols) <= 30 or any(not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", s) for s in symbols):
        raise HTTPException(422, "Supply 1 to 30 valid stock/ETF symbols")
    key = (tuple(symbols), request.horizon, request.cost_bps)
    with _lock:
        for job_id, job in list(_jobs.items()):
            if job["status"] != "running" and time.time()-job["created"] > 300:
                del _jobs[job_id]
        for job_id, job in _jobs.items():
            if job["key"] == key and job["status"] != "failed":
                return {"job_id": job_id, "status": job["status"]}
        if any(j["status"] == "running" for j in _jobs.values()) or len(_jobs) >= 10:
            raise HTTPException(429, "A scan is already running; retry after it finishes", headers={"Retry-After": "10"})
        job_id = uuid4().hex
        _jobs[job_id] = {"key": key, "status": "running", "created": time.time(), "completed": 0, "total": len(symbols)}

    def progress(completed, total):
        with _lock:
            _jobs[job_id].update(completed=completed, total=total)

    def run():
        try:
            result = build_board(symbols, request.horizon, request.cost_bps, progress)
            with _lock:
                _jobs[job_id].update(status="complete", result=result)
        except Exception:
            with _lock:
                _jobs[job_id].update(status="failed", error="Scan unavailable; check market-data configuration")
    _pool.submit(run)
    return {"job_id": job_id, "status": "running"}


@router.get("/{job_id}")
def get_scan(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            raise HTTPException(404, "Scan expired or service restarted; run a new scan")
        return {k: v for k, v in job.items() if k not in {"key", "created"}}
