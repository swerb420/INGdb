import os

import pandas as pd

os.environ.setdefault("ALPHA_VANTAGE_API_KEY", "test")
os.environ.setdefault("ALPHAVANTAGE_API_KEY", "test")
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
