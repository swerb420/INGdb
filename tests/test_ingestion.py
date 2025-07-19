import os
import sys

import pandas as pd

os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "test")
os.environ.setdefault("FRED_API_KEY", "test")
import importlib  # noqa: E402

import trading_intel.config as config  # noqa: E402

importlib.reload(config)  # ensure env var picked up
from trading_intel import ingestion  # noqa: E402


def test_fetch_crypto_error(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ingestion.requests, "get", fail)
    df = ingestion.fetch_crypto()
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_fetch_stock_error(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr(ingestion.requests, "get", fail)
    df = ingestion.fetch_stock()
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_fetch_yfinance_error(monkeypatch):
    class DummyTicker:
        def __init__(self, *args, **kwargs):
            pass

        def history(self, *args, **kwargs):
            raise RuntimeError("yf fail")

    dummy = type("mod", (), {"Ticker": DummyTicker})
    monkeypatch.setitem(sys.modules, "yfinance", dummy)
    df = ingestion.fetch_yfinance()
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_fetch_fred_error(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("fred fail")

    monkeypatch.setattr(ingestion.requests, "get", fail)
    df = ingestion.fetch_fred()
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_fetch_dune_error(monkeypatch):
    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def run_query_dataframe(self, query):
            raise RuntimeError("dune fail")

    monkeypatch.setattr(ingestion, "DuneClient", lambda *a, **k: DummyClient())
    df = ingestion.fetch_dune(1)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
