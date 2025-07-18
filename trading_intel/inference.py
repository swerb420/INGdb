import logging
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd
import sqlalchemy

from .config import DATABASE_URL, validate_env
from .features import create_features
from .ingestion import fetch_crypto, fetch_eth_chain, fetch_reddit, fetch_stock
from .logging_utils import setup_logging

logger = logging.getLogger(__name__)

engine = sqlalchemy.create_engine(DATABASE_URL)
onnx_path = Path(__file__).resolve().parent / "lstm_model.onnx"
if not onnx_path.exists():
    logger.error("ONNX model not found at %s", onnx_path)
    raise SystemExit(1)
sess = ort.InferenceSession(str(onnx_path))


def main() -> None:
    """Run the hourly inference loop."""
    while True:
        t0 = time.time()
        fetch_crypto()
        fetch_stock()
        fetch_eth_chain()
        fetch_reddit()
        create_features()
        df = pd.read_sql("features", engine).iloc[-1:]
        features = ["price_diff", "ema_12", "sentiment_score"]
        X = np.expand_dims(
            df[features].values.astype(np.float32),
            axis=1,
        )
        pred = sess.run(None, {"input": X})[0].squeeze()
        logger.info("%s \u2192 Prediction: %s", time.asctime(), pred)
        time.sleep(max(0, 3600 - (time.time() - t0)))


if __name__ == "__main__":
    validate_env()
    setup_logging()
    main()
