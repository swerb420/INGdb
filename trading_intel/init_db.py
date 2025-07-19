import logging

import sqlalchemy
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
)

from .config import DATABASE_URL, validate_env
from .logging_utils import setup_logging

logger = logging.getLogger(__name__)
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata = MetaData()

price_data = Table(
    "price_data",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("timestamp", DateTime, index=True),
    Column("open", Float),
    Column("high", Float),
    Column("low", Float),
    Column("close", Float),
    Column("volume", Float),
    Column("price", Float),
    Column("dividends", Float),
    Column("stock_splits", Float),
    Column("symbol", String(50), nullable=False),
    Column("type", String(50), nullable=False),
)

reddit_data = Table(
    "reddit_data",
    metadata,
    Column("id", String(30), primary_key=True),
    Column("timestamp", DateTime, index=True),
    Column("title", String),
    Column("selftext", String),
    Column("sub", String(100)),
)


def create_tables() -> None:
    """Create database tables defined in this module."""
    metadata.create_all(engine)
    logger.info("\u2705 Database tables created.")


if __name__ == "__main__":
    validate_env()
    setup_logging()
    create_tables()
