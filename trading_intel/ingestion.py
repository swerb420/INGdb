import logging
from datetime import datetime

import pandas as pd
import requests
import sqlalchemy
from alpha_vantage.timeseries import TimeSeries
from praw import Reddit
from web3 import Web3

from .config import API_KEYS, DATABASE_URL, LOG_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename=LOG_FILE if LOG_FILE else None,
)
logger = logging.getLogger(__name__)

engine = sqlalchemy.create_engine(DATABASE_URL)
ts = TimeSeries(key=API_KEYS["ALPHA_VANTAGE"], output_format="pandas")
reddit = Reddit(
    client_id=API_KEYS["REDDIT_CLIENT_ID"],
    client_secret=API_KEYS["REDDIT_CLIENT_SECRET"],
    user_agent="ti-app",
)


def _handle_error(msg: str, exc: Exception) -> None:
    """Log the error message and exception details."""
    logger.error("%s: %s", msg, exc)


# Crypto
def fetch_crypto(coin: str = "bitcoin", vs: str = "usd") -> pd.DataFrame:
    """Fetch recent cryptocurrency prices from CoinGecko.

    Returns an empty ``DataFrame`` on failure.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    try:
        resp = requests.get(
            url,
            params={"vs_currency": vs, "days": "7"},
            timeout=10,
        )
        resp.raise_for_status()
        df = pd.DataFrame(
            resp.json()["prices"], columns=["timestamp", "price"]
        )  # noqa: E501
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["type"] = "crypto"
        df["symbol"] = coin
        df.to_sql("price_data", engine, if_exists="append", index=False)
        logger.info("Fetched crypto data for %s", coin)
        return df
    except Exception as exc:  # noqa: BLE001
        _handle_error("Failed to fetch crypto data", exc)
        return pd.DataFrame()


# Stocks
def fetch_stock(symbol: str = "AAPL") -> pd.DataFrame:
    """Fetch hourly stock data using Alpha Vantage."""
    try:
        df, _ = ts.get_intraday(symbol, interval="60min", outputsize="compact")
        df.reset_index(inplace=True)
        df.rename(
            columns={
                "date": "timestamp",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            },
            inplace=True,
        )
        df["symbol"] = symbol
        df["type"] = "stock"
        df.to_sql("price_data", engine, if_exists="append", index=False)
        logger.info("Fetched stock data for %s", symbol)
        return df
    except Exception as exc:  # noqa: BLE001
        _handle_error(f"Failed to fetch stock data for {symbol}", exc)
        return pd.DataFrame()


# On-chain (Ethereum)
def fetch_eth_chain() -> pd.DataFrame:
    """Fetch the latest Ethereum block information."""
    try:
        w3 = Web3(Web3.HTTPProvider("https://cloudflare-eth.com"))
        block = w3.eth.get_block("latest")
        df = pd.DataFrame(
            [
                {
                    **dict(block),
                    "timestamp": datetime.utcfromtimestamp(block.timestamp),
                    "symbol": "ETH",
                    "type": "onchain",
                }
            ]
        )
        df.to_sql("onchain_data", engine, if_exists="append", index=False)
        logger.info("Fetched latest Ethereum block")
        return df
    except Exception as exc:  # noqa: BLE001
        _handle_error("Failed to fetch Ethereum block", exc)
        return pd.DataFrame()


# Reddit
def fetch_reddit(sub: str = "CryptoCurrency", limit: int = 50) -> pd.DataFrame:
    """Fetch recent Reddit submissions from ``sub``."""
    try:
        posts = reddit.subreddit(sub).new(limit=limit)
        df = pd.DataFrame(
            [
                {
                    "id": p.id,
                    "timestamp": datetime.utcfromtimestamp(p.created_utc),
                    "title": p.title,
                    "selftext": p.selftext,
                    "sub": sub,
                }
                for p in posts
            ]
        )
        df.to_sql("reddit_data", engine, if_exists="append", index=False)
        logger.info("Fetched %d Reddit posts from %s", len(df), sub)
        return df
    except Exception as exc:  # noqa: BLE001
        _handle_error(f"Failed to fetch Reddit posts from {sub}", exc)
        return pd.DataFrame()


if __name__ == "__main__":
    fetch_crypto()
    fetch_stock()
    fetch_eth_chain()
    fetch_reddit()
