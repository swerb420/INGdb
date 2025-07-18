import logging
from pathlib import Path

import pandas as pd
import sqlalchemy
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split

from .config import DATABASE_URL
from .logging_utils import setup_logging

logger = logging.getLogger(__name__)

engine = sqlalchemy.create_engine(DATABASE_URL)
lstm_path = Path(__file__).resolve().parent / "lstm.pth"


class SimpleLSTM(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, 32, batch_first=True)
        self.fc = nn.Linear(32, 1)

    def forward(self, x):
        return self.fc(self.lstm(x)[0][:, -1, :])


def train():
    df = pd.read_sql("features", engine)
    X = df[["price_diff", "ema_12", "sentiment_score"]].values
    y = df["price_diff"].shift(-1).fillna(0).values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    X_train = torch.FloatTensor(X_train).unsqueeze(1)
    y_train = torch.FloatTensor(y_train)
    model = SimpleLSTM(X_train.shape[-1])
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    for epoch in range(50):
        model.train()
        optimizer.zero_grad()
        loss = criterion(model(X_train).squeeze(), y_train)
        loss.backward()
        optimizer.step()
    torch.save(model.state_dict(), lstm_path)
    logger.info("\U0001f389 Model trained, loss: %s", loss.item())


if __name__ == "__main__":
    setup_logging()
    train()
