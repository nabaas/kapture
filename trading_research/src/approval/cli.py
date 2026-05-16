"""CLI for acting on proposals.

This is the **only** authorized path to send an order to the broker.
Run from a trusted shell; do not expose this CLI over a network.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict

from . import store


def _cmd_list(_: argparse.Namespace) -> int:
    store.expire_stale()
    rows = store.list_open()
    if not rows:
        print("(no open proposals)")
        return 0
    for p in rows:
        print(
            f"{p.id}  {p.side.upper():4}  {p.symbol:10}  "
            f"qty={p.qty}  notional=${p.notional_usd}  score={p.score:+.2f}  "
            f"reason={p.reason}"
        )
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    p = store.load(args.id)
    import json as _json
    print(_json.dumps(asdict(p), indent=2))
    return 0


def _cmd_reject(args: argparse.Namespace) -> int:
    p = store.load(args.id)
    if p.status != "open":
        print(f"refusing to reject: status={p.status}", file=sys.stderr)
        return 2
    p.status = "rejected"
    store.save(p)
    print(f"rejected {p.id}")
    return 0


def _cmd_approve(args: argparse.Namespace) -> int:
    from ..broker.alpaca_orders import submit

    p = store.load(args.id)
    store.expire_stale()
    p = store.load(p.id)  # reload after expire pass
    if p.status != "open":
        print(f"refusing to approve: status={p.status}", file=sys.stderr)
        return 2

    p.status = "approved"
    store.save(p)
    response = submit(p, paper=not args.live)
    p.status = "filled"
    store.save(p)
    store.record_fill(p, response)
    print(f"approved + submitted {p.id} (paper={not args.live})")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="approval")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list").set_defaults(func=_cmd_list)

    s = sub.add_parser("show"); s.add_argument("id"); s.set_defaults(func=_cmd_show)
    s = sub.add_parser("reject"); s.add_argument("id"); s.set_defaults(func=_cmd_reject)

    s = sub.add_parser("approve")
    s.add_argument("id")
    s.add_argument(
        "--live",
        action="store_true",
        help="route to LIVE broker (also requires "
             "TRADING_RESEARCH_I_UNDERSTAND_THE_RISK=yes)",
    )
    s.set_defaults(func=_cmd_approve)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
