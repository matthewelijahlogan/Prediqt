from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import os
import re
from threading import Lock
from typing import Literal
from uuid import uuid4


ProposalStatus = Literal["PENDING_APPROVAL", "SUBMITTING", "SUBMITTED", "REJECTED"]


@dataclass
class TradeProposal:
    proposal_id: str
    symbol: str
    side: Literal["buy", "sell"]
    notional: float
    rationale: str
    status: ProposalStatus
    created_at: str
    client_order_id: str
    broker_order_id: str | None = None
    broker_status: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class ProposalStore:
    def __init__(self):
        self._items: dict[str, TradeProposal] = {}
        self._lock = Lock()

    def create(self, symbol: str, side: str, notional: float, rationale: str) -> TradeProposal:
        normalized_symbol = symbol.strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", normalized_symbol):
            raise ValueError("Invalid stock symbol")
        if side not in {"buy", "sell"}:
            raise ValueError("Side must be buy or sell")
        maximum = float(os.environ.get("AUTOMATION_MAX_NOTIONAL", "100"))
        if notional <= 0 or notional > maximum:
            raise ValueError(f"Notional must be between $0.01 and ${maximum:.2f}")

        with self._lock:
            existing = next(
                (
                    item for item in reversed(list(self._items.values()))
                    if item.symbol == normalized_symbol
                    and item.side == side
                    and item.status == "PENDING_APPROVAL"
                ),
                None,
            )
            if existing:
                return existing

            proposal_id = str(uuid4())
            proposal = TradeProposal(
                proposal_id=proposal_id,
                symbol=normalized_symbol,
                side=side,
                notional=round(float(notional), 2),
                rationale=rationale.strip()[:500],
                status="PENDING_APPROVAL",
                created_at=datetime.now(timezone.utc).isoformat(),
                client_order_id=f"prediqt-{proposal_id.replace('-', '')[:24]}",
            )
            self._items[proposal_id] = proposal
            return proposal

    def list(self) -> list[TradeProposal]:
        with self._lock:
            return list(reversed(list(self._items.values())))

    def get(self, proposal_id: str) -> TradeProposal | None:
        with self._lock:
            return self._items.get(proposal_id)

    def begin_submission(self, proposal_id: str) -> TradeProposal:
        with self._lock:
            proposal = self._items.get(proposal_id)
            if not proposal:
                raise KeyError("Proposal not found")
            if proposal.status == "SUBMITTED":
                return proposal
            if proposal.status != "PENDING_APPROVAL":
                raise ValueError(f"Proposal cannot be approved from {proposal.status}")
            proposal.status = "SUBMITTING"
            proposal.error = None
            return proposal

    def submission_succeeded(self, proposal_id: str, order: dict) -> TradeProposal:
        with self._lock:
            proposal = self._items[proposal_id]
            proposal.status = "SUBMITTED"
            proposal.broker_order_id = str(order.get("id")) if order.get("id") else None
            proposal.broker_status = order.get("status")
            proposal.error = None
            return proposal

    def submission_failed(self, proposal_id: str, error: str) -> TradeProposal:
        with self._lock:
            proposal = self._items[proposal_id]
            proposal.status = "PENDING_APPROVAL"
            proposal.error = error[:500]
            return proposal

    def reject(self, proposal_id: str) -> TradeProposal:
        with self._lock:
            proposal = self._items.get(proposal_id)
            if not proposal:
                raise KeyError("Proposal not found")
            if proposal.status != "PENDING_APPROVAL":
                raise ValueError(f"Proposal cannot be rejected from {proposal.status}")
            proposal.status = "REJECTED"
            proposal.error = None
            return proposal


proposal_store = ProposalStore()
