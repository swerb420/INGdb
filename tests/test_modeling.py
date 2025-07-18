import pandas as pd

from trading_intel import modeling


def test_train_creates_model(tmp_path, monkeypatch):
    df = pd.DataFrame(
        {
            "price_diff": [0.1, 0.2, 0.3, 0.4, 0.5],
            "ema_12": [1, 2, 3, 4, 5],
            "sentiment_score": [0.1, 0.2, 0.3, 0.4, 0.5],
        }
    )

    def fake_read_sql(table, engine):
        return df.copy()

    monkeypatch.setattr(modeling.pd, "read_sql", fake_read_sql)
    monkeypatch.setattr(modeling, "lstm_path", tmp_path / "lstm.pth")
    monkeypatch.setattr(modeling, "range", lambda n: range(1))

    modeling.train()

    assert modeling.lstm_path.exists()
