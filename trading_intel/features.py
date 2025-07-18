import pandas as pd, numpy as np, sqlalchemy, networkx as nx
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import DATABASE_URL

engine = sqlalchemy.create_engine(DATABASE_URL)
vader = SentimentIntensityAnalyzer()

def create_features():
    query = """
        SELECT p.*, r.title
        FROM price_data p
        LEFT JOIN reddit_data r
          ON DATE_TRUNC('hour', p.timestamp) = DATE_TRUNC('hour', r.timestamp)
        ORDER BY p.timestamp
    """
    df = pd.read_sql(query, engine)
    df["hour"] = df.timestamp.dt.hour
    df["price_diff"] = df.price.pct_change()
    df["ema_12"] = df.price.ewm(span=12).mean()
    df["sentiment_score"] = df.title.apply(
        lambda t: vader.polarity_scores(t)["compound"] if isinstance(t, str) and t else 0.0
    )
    df.dropna(subset=["price_diff", "ema_12"], inplace=True)
    df.to_sql("features", engine, if_exists="replace", index=False)

if __name__ == "__main__":
    create_features()
