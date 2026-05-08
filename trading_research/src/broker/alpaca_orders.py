"""Submit an APPROVED proposal to Alpaca.

Hard refuses to submit anything that wasn't first approved through
`approval/cli.py`. Hard refuses to submit a live order without the
explicit acknowledgement env var.
"""

from __future__ import annotations

import os
from typing import Any

from ..approval.store import Proposal
from ..data.alpaca_client import LIVE_ACK_ENV, trading_client


def submit(p: Proposal, *, paper: bool = True) -> dict[str, Any]:
    """Submit a proposal to Alpaca. Returns a dict of the broker response.

    Caller (approval CLI) must have set p.status='approved' before calling.
    """
    if p.status != "approved":
        raise PermissionError(
            f"refusing to submit proposal {p.id}: status={p.status!r}"
        )
    if not paper and os.environ.get(LIVE_ACK_ENV, "").lower() != "yes":
        raise PermissionError(
            f"refusing live submission: set {LIVE_ACK_ENV}=yes to opt in"
        )

    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest

    client = trading_client(paper=paper)
    side = OrderSide.BUY if p.side.lower() == "buy" else OrderSide.SELL

    req = MarketOrderRequest(
        symbol=p.symbol,
        qty=p.qty,
        side=side,
        time_in_force=TimeInForce.GTC,
    )
    order = client.submit_order(req)
    raw = order.model_dump() if hasattr(order, "model_dump") else dict(order)
    return {"id": str(raw.get("id")), "status": str(raw.get("status")), "raw": raw}
