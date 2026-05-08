"""On-disk store for proposals and fills.

Each proposal is a JSON file under `proposals/<id>.json`. Approving a
proposal moves it to `fills/<id>.json` (with the broker response)
or marks it rejected.

Proposals expire after `ttl_minutes`; expired proposals can never be
approved. This is the single source of truth that the CLI and the
broker adapter both use; nothing else may write to these directories.
"""

from __future__ import annotations

import json
import secrets
import string
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent.parent
PROPOSALS_DIR = ROOT / "proposals"
FILLS_DIR = ROOT / "fills"


def _alphanum_id(n: int = 8) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


@dataclass
class Proposal:
    id: str
    symbol: str
    side: str               # "buy" | "sell"
    qty: float
    notional_usd: float
    reason: str
    created_at: str
    expires_at: float       # unix ts
    score: float = 0.0
    status: str = "open"    # open | approved | rejected | expired | filled
    extra: dict = field(default_factory=dict)


def _now() -> float:
    return time.time()


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_proposal(
    *,
    symbol: str,
    side: str,
    qty: float,
    notional_usd: float,
    reason: str,
    score: float = 0.0,
    ttl_minutes: int = 30,
    extra: Optional[dict] = None,
) -> Proposal:
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    pid = _alphanum_id()
    p = Proposal(
        id=pid,
        symbol=symbol,
        side=side,
        qty=qty,
        notional_usd=notional_usd,
        reason=reason,
        created_at=_iso_now(),
        expires_at=_now() + ttl_minutes * 60,
        score=score,
        extra=extra or {},
    )
    (PROPOSALS_DIR / f"{pid}.json").write_text(json.dumps(asdict(p), indent=2))
    return p


def load(pid: str) -> Proposal:
    path = PROPOSALS_DIR / f"{pid}.json"
    if not path.exists():
        raise FileNotFoundError(f"no proposal {pid}")
    raw = json.loads(path.read_text())
    return Proposal(**raw)


def save(p: Proposal) -> None:
    (PROPOSALS_DIR / f"{p.id}.json").write_text(json.dumps(asdict(p), indent=2))


def list_open() -> list[Proposal]:
    if not PROPOSALS_DIR.exists():
        return []
    out: list[Proposal] = []
    for path in sorted(PROPOSALS_DIR.glob("*.json")):
        try:
            raw = json.loads(path.read_text())
            p = Proposal(**raw)
        except Exception:
            continue
        if p.status == "open" and p.expires_at >= _now():
            out.append(p)
    return out


def expire_stale() -> int:
    n = 0
    for path in PROPOSALS_DIR.glob("*.json"):
        raw = json.loads(path.read_text())
        if raw["status"] == "open" and raw["expires_at"] < _now():
            raw["status"] = "expired"
            path.write_text(json.dumps(raw, indent=2))
            n += 1
    return n


def record_fill(p: Proposal, broker_response: dict) -> Path:
    FILLS_DIR.mkdir(parents=True, exist_ok=True)
    path = FILLS_DIR / f"{p.id}.json"
    path.write_text(
        json.dumps(
            {
                "proposal": asdict(p),
                "broker_response": broker_response,
                "filled_at": _iso_now(),
            },
            indent=2,
            default=str,
        )
    )
    return path
