import importlib  # noqa: E402

import pytest  # noqa: E402

import trading_intel.config as config  # noqa: E402


def reload_config(monkeypatch, env):
    for k, v in env.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, v)
    return importlib.reload(config)


def test_validate_env_missing(monkeypatch):
    conf = reload_config(
        monkeypatch,
        {
            "DATABASE_URL": None,
            "ALPHA_VANTAGE_API_KEY": None,
            "FRED_API_KEY": None,
            "REDDIT_CLIENT_ID": None,
            "REDDIT_CLIENT_SECRET": None,
        },
    )
    with pytest.raises(RuntimeError):
        conf.validate_env()


def test_validate_env_present(monkeypatch):
    conf = reload_config(
        monkeypatch,
        {
            "DATABASE_URL": "sqlite:///:memory:",
            "ALPHA_VANTAGE_API_KEY": "x",
            "FRED_API_KEY": "x",
            "REDDIT_CLIENT_ID": "x",
            "REDDIT_CLIENT_SECRET": "x",
        },
    )
    conf.validate_env()
