import pandas as pd, numpy as np, sqlalchemy, networkx as nx, logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import DATABASE_URL, LOG_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename=LOG_FILE if LOG_FILE else None,
)
logger = logging.getLogger(__name__)

engine = sqlalchemy.create_engine(DATABASE_URL)
vader = SentimentIntensityAnalyzer()

def create_features():
    df = pd.read_sql("SELECT * FROM price_data ORDER BY timestamp", engine)
    df["hour"] = df.timestamp.dt.hour
    df["price_diff"] = df.price.pct_change()
    df["ema_12"] = df.price.ewm(span=12).mean()
    df["sentiment_score"] = df.title.apply(lambda t: vader.polarity_scores(t)["compound"])
    df.dropna(inplace=True)
    df.to_sql("features", engine, if_exists="replace", index=False)
    logger.info("Features table created with %d rows", len(df))

if __name__ == "__main__":
    create_features()
