import importlib

import pandas as pd

import trading_intel.config as config  # noqa: E402


def reload_features(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    importlib.reload(config)
    import trading_intel.features as features  # noqa: E402
    return importlib.reload(features)


def test_create_features_missing_tables(monkeypatch):
    features = reload_features(monkeypatch)
    df = features.create_features()
    assert isinstance(df, pd.DataFrame)
    assert df.empty
