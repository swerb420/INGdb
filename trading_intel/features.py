import logging

import pandas as pd
import sqlalchemy
from sqlalchemy.exc import DatabaseError
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .config import DATABASE_URL
from .logging_utils import setup_logging

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
    try:
        df = pd.read_sql(query, engine)
    except DatabaseError as exc:  # tables may not exist
        logger.error("Failed to read tables for features: %s", exc)
        return pd.DataFrame()
    df["hour"] = df.timestamp.dt.hour
    df["price_diff"] = df.price.pct_change()
    df["ema_12"] = df.price.ewm(span=12).mean()
    df["sentiment_score"] = df.title.apply(_sentiment)
    df.dropna(subset=["price_diff", "ema_12"], inplace=True)
    df.to_sql("features", engine, if_exists="replace", index=False)
    logger.info("Features table created with %d rows", len(df))


if __name__ == "__main__":
    setup_logging()
    create_features()
