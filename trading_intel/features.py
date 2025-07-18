import logging

import pandas as pd
import sqlalchemy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .config import DATABASE_URL, LOG_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename=LOG_FILE if LOG_FILE else None,
)
logger = logging.getLogger(__name__)


engine = sqlalchemy.create_engine(DATABASE_URL)
vader = SentimentIntensityAnalyzer()


def _sentiment(text: str) -> float:
    return (
        vader.polarity_scores(text)["compound"]
        if isinstance(text, str) and text
        else 0.0
    )


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
    df["sentiment_score"] = df.title.apply(_sentiment)
    df.dropna(subset=["price_diff", "ema_12"], inplace=True)
    df.to_sql("features", engine, if_exists="replace", index=False)
    logger.info("Features table created with %d rows", len(df))


if __name__ == "__main__":
    create_features()
