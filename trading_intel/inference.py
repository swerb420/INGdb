import onnxruntime as ort, numpy as np, logging
from ingestion import fetch_crypto, fetch_reddit, fetch_stock, fetch_eth_chain
from features import create_features
from config import DATABASE_URL, LOG_FILE
import sqlalchemy, time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename=LOG_FILE if LOG_FILE else None,
)
logger = logging.getLogger(__name__)

engine = sqlalchemy.create_engine(DATABASE_URL)
sess = ort.InferenceSession("lstm_model.onnx")

while True:
    t0 = time.time()
    fetch_crypto(); fetch_stock(); fetch_eth_chain(); fetch_reddit()
    create_features()
    df = sqlalchemy.read_sql("features", engine).iloc[-1:]
    X = np.expand_dims(df[["price_diff","ema_12","sentiment_score"]].values.astype(np.float32), axis=1)
    pred = sess.run(None, {"input": X})[0].squeeze()
    logger.info("%s \u2192 Prediction: %s", time.asctime(), pred)
    time.sleep(max(0, 3600 - (time.time() - t0)))
