"""Tests for the proposal store + approval safety guards."""

from __future__ import annotations

import os
import time

import pytest

from trading_research.src.approval import store


@pytest.fixture(autouse=True)
def _isolated_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "PROPOSALS_DIR", tmp_path / "proposals")
    monkeypatch.setattr(store, "FILLS_DIR", tmp_path / "fills")
    yield


def _make() -> store.Proposal:
    return store.create_proposal(
        symbol="BTC/USD",
        side="buy",
        qty=0.001,
        notional_usd=50.0,
        reason="unit test",
        ttl_minutes=30,
    )


def test_create_and_load() -> None:
    p = _make()
    loaded = store.load(p.id)
    assert loaded.symbol == "BTC/USD"
    assert loaded.status == "open"


def test_expire_stale_marks_old() -> None:
    p = _make()
    p.expires_at = time.time() - 1  # already expired
    store.save(p)
    assert store.expire_stale() == 1
    assert store.load(p.id).status == "expired"


def test_list_open_excludes_expired() -> None:
    p = _make()
    p.expires_at = time.time() - 1
    store.save(p)
    store.expire_stale()
    assert store.list_open() == []


def test_broker_refuses_unapproved_proposal() -> None:
    """The broker must never submit a proposal whose status != approved."""
    from trading_research.src.broker import alpaca_orders

    p = _make()
    assert p.status == "open"
    with pytest.raises(PermissionError):
        alpaca_orders.submit(p, paper=True)


def test_broker_refuses_live_without_ack(monkeypatch) -> None:
    from trading_research.src.broker import alpaca_orders
    from trading_research.src.data.alpaca_client import LIVE_ACK_ENV

    monkeypatch.delenv(LIVE_ACK_ENV, raising=False)
    p = _make()
    p.status = "approved"
    with pytest.raises(PermissionError):
        alpaca_orders.submit(p, paper=False)
