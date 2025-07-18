import logging
import time
from datetime import datetime

import pandas as pd
import requests
import sqlalchemy
from alpha_vantage.timeseries import TimeSeries
from praw import Reddit
from web3 import Web3

from .config import API_KEYS, DATABASE_URL
from .logging_utils import setup_logging

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
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "60min",
        "apikey": API_KEYS["ALPHA_VANTAGE"],
        "outputsize": "compact",
    }
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()["Time Series (60min)"]
            df = (
                pd.DataFrame.from_dict(data, orient="index")
                .rename(
                    columns={
                        "1. open": "open",
                        "2. high": "high",
                        "3. low": "low",
                        "4. close": "close",
                        "5. volume": "volume",
                    }
                )
                .reset_index()
                .rename(columns={"index": "timestamp"})
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["symbol"] = symbol
            df["type"] = "stock"
            df.to_sql("price_data", engine, if_exists="append", index=False)
            logger.info("Fetched stock data for %s", symbol)
            return df
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Attempt %d failed to fetch stock data for %s: %s",
                attempt + 1,
                symbol,
                exc,
            )
            time.sleep(2**attempt)
    _handle_error(
        f"Failed to fetch stock data for {symbol}",
        Exception("max retries"),
    )
    return pd.DataFrame()


# On-chain (Ethereum)
def fetch_eth_chain() -> pd.DataFrame:
    """Fetch the latest Ethereum block information."""
    for attempt in range(3):
        try:
            w3 = Web3(
                Web3.HTTPProvider(
                    "https://cloudflare-eth.com",
                    request_kwargs={"timeout": 15},
                )
            )
            block = w3.eth.get_block("latest")
            ts = datetime.utcfromtimestamp(block.timestamp)
            df = pd.DataFrame(
                [
                    {
                        **dict(block),
                        "timestamp": ts,
                        "symbol": "ETH",
                        "type": "onchain",
                    }
                ]
            )
            df.to_sql("onchain_data", engine, if_exists="append", index=False)
            logger.info("Fetched latest Ethereum block")
            return df
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Attempt %d failed to fetch Ethereum block: %s",
                attempt + 1,
                exc,
            )
            time.sleep(2**attempt)
    _handle_error(
        "Failed to fetch Ethereum block",
        Exception("max retries"),
    )
    return pd.DataFrame()


# Reddit
def fetch_reddit(sub: str = "CryptoCurrency", limit: int = 50) -> pd.DataFrame:
    """Fetch recent Reddit submissions from ``sub``."""
    url = f"https://www.reddit.com/r/{sub}/new.json"
    headers = {"User-Agent": "ti-app"}
    params = {"limit": limit}
    for attempt in range(3):
        try:
            resp = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            posts = resp.json()["data"]["children"]
            df = pd.DataFrame(
                [
                    {
                        "id": p["data"]["id"],
                        "timestamp": datetime.utcfromtimestamp(
                            p["data"]["created_utc"]
                        ),
                        "title": p["data"]["title"],
                        "selftext": p["data"].get("selftext", ""),
                        "sub": sub,
                    }
                    for p in posts
                ]
            )
            df.to_sql("reddit_data", engine, if_exists="append", index=False)
            logger.info("Fetched %d Reddit posts from %s", len(df), sub)
            return df
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Attempt %d failed to fetch Reddit posts from %s: %s",
                attempt + 1,
                sub,
                exc,
            )
            time.sleep(2**attempt)
    _handle_error(
        f"Failed to fetch Reddit posts from {sub}",
        Exception("max retries"),
    )
    return pd.DataFrame()


if __name__ == "__main__":
    setup_logging()
    fetch_crypto()
    fetch_stock()
    fetch_eth_chain()
    fetch_reddit()
