import ccxt, requests, pandas as pd, sqlalchemy, logging
from alpha_vantage.timeseries import TimeSeries
from praw import Reddit
from web3 import Web3
from datetime import datetime
from psycopg2 import sql
from config import DATABASE_URL, API_KEYS, LOG_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename=LOG_FILE if LOG_FILE else None,
)
logger = logging.getLogger(__name__)

engine = sqlalchemy.create_engine(DATABASE_URL)
ts = TimeSeries(key=API_KEYS["ALPHA_VANTAGE"], output_format='pandas')
reddit = Reddit(client_id=API_KEYS["REDDIT_CLIENT_ID"],
                client_secret=API_KEYS["REDDIT_CLIENT_SECRET"],
                user_agent="ti-app")

# Crypto
def fetch_crypto(coin="bitcoin", vs="usd"):
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
    resp = requests.get(url, params={"vs_currency": vs, "days": "7"})
    df = pd.DataFrame(resp.json()["prices"], columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["type"] = "crypto"; df["symbol"] = coin
    df.to_sql("price_data", engine, if_exists="append", index=False)
    logger.info("Fetched crypto data for %s", coin)

# Stocks
def fetch_stock(symbol="AAPL"):
    df, _ = ts.get_intraday(symbol, interval='60min', outputsize='compact')
    df.reset_index(inplace=True)
    df.rename(columns={"date":"timestamp","open":"open","high":"high","low":"low","close":"close","volume":"volume"}, inplace=True)
    df["symbol"] = symbol; df["type"] = "stock"
    df.to_sql("price_data", engine, if_exists="append", index=False)
    logger.info("Fetched stock data for %s", symbol)

# On-chain (Ethereum)
def fetch_eth_chain():
    w3 = Web3(Web3.HTTPProvider("https://cloudflare-eth.com"))
    block = w3.eth.get_block("latest")
    df = pd.DataFrame([{**dict(block), "timestamp": datetime.utcfromtimestamp(block.timestamp), "symbol":"ETH", "type":"onchain"}])
    df.to_sql("onchain_data", engine, if_exists="append", index=False)
    logger.info("Fetched latest Ethereum block")

# Reddit
def fetch_reddit(sub="CryptoCurrency", limit=50):
    posts = reddit.subreddit(sub).new(limit=limit)
    df = pd.DataFrame([{"id":p.id,"timestamp":datetime.utcfromtimestamp(p.created_utc),
                        "title":p.title, "selftext":p.selftext, "sub":sub} for p in posts])
    df.to_sql("reddit_data", engine, if_exists="append", index=False)
    logger.info("Fetched %d Reddit posts from %s", len(df), sub)

if __name__ == "__main__":
    fetch_crypto()
    fetch_stock()
    fetch_eth_chain()
    fetch_reddit()
