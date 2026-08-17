from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.alpaca_paper import submit_market_order
from backend.automation import proposal_store


router = APIRouter(prefix="/api/automation", tags=["automation"])


class ProposalRequest(BaseModel):
    symbol: str
    side: str
    notional: float = Field(gt=0)
    rationale: str = ""


@router.get("/status")
def automation_status():
    import os

    connected = bool(
        os.environ.get("ALPACA_PAPER_API_KEY")
        and os.environ.get("ALPACA_PAPER_SECRET_KEY")
    )
    return {
        "mode": "PAPER",
        "approval_required": True,
        "broker": "alpaca",
        "connected": connected,
        "maximum_notional": float(os.environ.get("AUTOMATION_MAX_NOTIONAL", "100")),
    }


@router.get("/proposals")
def list_proposals():
    return {"items": [item.to_dict() for item in proposal_store.list()]}


@router.post("/proposals")
def create_proposal(payload: ProposalRequest):
    try:
        return proposal_store.create(
            payload.symbol,
            payload.side.lower(),
            payload.notional,
            payload.rationale,
        ).to_dict()
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: str):
    try:
        proposal = proposal_store.begin_submission(proposal_id)
        if proposal.status == "SUBMITTED":
            return proposal.to_dict()
        try:
            order = submit_market_order(
                proposal.symbol,
                proposal.side,
                proposal.notional,
                proposal.client_order_id,
            )
        except Exception as error:
            proposal_store.submission_failed(proposal_id, str(error))
            raise HTTPException(status_code=503, detail=str(error)) from error
        return proposal_store.submission_succeeded(proposal_id, order).to_dict()
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: str):
    try:
        return proposal_store.reject(proposal_id).to_dict()
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
