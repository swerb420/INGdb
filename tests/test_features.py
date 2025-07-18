import pandas as pd
import pandas.testing as pdt

from trading_intel import features


def test_create_features(monkeypatch):
    sample = pd.DataFrame(
        {
            "timestamp": pd.date_range("2021-01-01", periods=3, freq="H"),
            "price": [100.0, 110.0, 120.0],
            "title": ["a", "b", "c"],
        }
    )

    def fake_read_sql(query, engine):
        return sample.copy()

    captured = {}

    def fake_to_sql(self, name, engine, if_exists="replace", index=False):
        captured["df"] = self.copy()
        captured["name"] = name
        captured["if_exists"] = if_exists
        captured["index"] = index

    monkeypatch.setattr(features.pd, "read_sql", fake_read_sql)
    monkeypatch.setattr(pd.DataFrame, "to_sql", fake_to_sql)
    monkeypatch.setattr(features, "_sentiment", lambda text: 0.5)

    features.create_features()

    out = captured["df"].reset_index(drop=True)
    expected = sample.copy()
    expected["hour"] = expected.timestamp.dt.hour
    expected["price_diff"] = expected.price.pct_change()
    expected["ema_12"] = expected.price.ewm(span=12).mean()
    expected["sentiment_score"] = 0.5
    expected.dropna(subset=["price_diff", "ema_12"], inplace=True)
    expected = expected.reset_index(drop=True)

    pdt.assert_frame_equal(out, expected)
    assert captured["name"] == "features"
    assert captured["if_exists"] == "replace"
    assert not captured["index"]
