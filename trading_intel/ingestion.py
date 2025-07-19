import asyncio
import logging
import time
from datetime import datetime

import pandas as pd
import requests
import sqlalchemy
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from web3 import Web3

from .config import API_KEYS, DATABASE_URL, validate_env
from .logging_utils import setup_logging

logger = logging.getLogger(__name__)

engine = sqlalchemy.create_engine(DATABASE_URL)


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


# yfinance
def fetch_yfinance(symbol: str = "SPY", period: str = "1mo") -> pd.DataFrame:
    """Fetch historical stock data using the yfinance library.

    Parameters
    ----------
    symbol: str
        Stock ticker symbol.
    period: str
        Data period, defaults to one month.

    Returns
    -------
    pandas.DataFrame
        Price data or an empty DataFrame on failure.
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if df.empty:
            raise RuntimeError("No data returned")
        df = df.reset_index().rename(columns={"Date": "timestamp"})
        df["symbol"] = symbol
        df["type"] = "yfinance"
        df.to_sql("price_data", engine, if_exists="append", index=False)
        logger.info("Fetched yfinance data for %s", symbol)
        return df
    except Exception as exc:  # noqa: BLE001
        _handle_error("Failed to fetch yfinance data", exc)
        return pd.DataFrame()


# FRED
def fetch_fred(series: str = "DEXUSAL") -> pd.DataFrame:
    """Fetch a macroeconomic series from FRED."""
    api_key = API_KEYS.get("FRED", "")
    if not api_key:
        _handle_error("FRED_API_KEY not configured", Exception("missing key"))
        return pd.DataFrame()
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {"series_id": series, "api_key": api_key, "file_type": "json"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("observations", [])
        df = pd.DataFrame(data)
        if df.empty:
            raise RuntimeError("No observations")
        df = df.rename(columns={"value": "price", "date": "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["symbol"] = series
        df["type"] = "fred"
        df.to_sql("price_data", engine, if_exists="append", index=False)
        logger.info("Fetched FRED data for %s", series)
        return df
    except Exception as exc:  # noqa: BLE001
        _handle_error("Failed to fetch FRED data", exc)
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


# Dune Analytics
def fetch_dune(query_id: int = 0) -> pd.DataFrame:
    """Fetch query results from Dune Analytics.

    Parameters
    ----------
    query_id: int
        The ID of the Dune query to run.

    Returns
    -------
    pandas.DataFrame
        Query results or an empty DataFrame on failure.
    """
    api_key = API_KEYS.get("DUNE", "")
    if not api_key:
        _handle_error("DUNE_API_KEY not configured", Exception("missing key"))
        return pd.DataFrame()
    try:
        client = DuneClient(api_key)
        query = QueryBase(query_id=query_id)
        df = client.run_query_dataframe(query)
        df["query_id"] = query_id
        df.to_sql("dune_data", engine, if_exists="append", index=False)
        logger.info("Fetched Dune data for query %s", query_id)
        return df
    except Exception as exc:  # noqa: BLE001
        _handle_error("Failed to fetch Dune data", exc)
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


async def fetch_all() -> dict[str, pd.DataFrame]:
    """Fetch all data sources concurrently."""
    fetchers = {
        "crypto": fetch_crypto,
        "stock": fetch_stock,
        "yfinance": fetch_yfinance,
        "fred": fetch_fred,
        "eth_chain": fetch_eth_chain,
        "dune": fetch_dune,
        "reddit": fetch_reddit,
    }

    async def run(name: str, func) -> tuple[str, pd.DataFrame]:
        return name, await asyncio.to_thread(func)

    tasks = [run(n, f) for n, f in fetchers.items()]
    results: dict[str, pd.DataFrame] = {}
    for coro in asyncio.as_completed(tasks):
        name, df = await coro
        results[name] = df
    return results


if __name__ == "__main__":
    validate_env()
    setup_logging()
    asyncio.run(fetch_all())
