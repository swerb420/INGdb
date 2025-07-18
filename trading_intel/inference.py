import onnxruntime as ort, numpy as np
from ingestion import fetch_crypto, fetch_reddit, fetch_stock, fetch_eth_chain
from features import create_features
from config import DATABASE_URL
import sqlalchemy, time

engine = sqlalchemy.create_engine(DATABASE_URL)
sess = ort.InferenceSession("lstm_model.onnx")

while True:
    t0 = time.time()
    fetch_crypto(); fetch_stock(); fetch_eth_chain(); fetch_reddit()
    create_features()
    df = sqlalchemy.read_sql("features", engine).iloc[-1:]
    X = np.expand_dims(df[["price_diff","ema_12","sentiment_score"]].values.astype(np.float32), axis=1)
    pred = sess.run(None, {"input": X})[0].squeeze()
    print(time.asctime(), "→ Prediction:", pred)
    time.sleep(max(0, 3600 - (time.time() - t0)))
