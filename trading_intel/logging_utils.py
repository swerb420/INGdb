import logging

from .config import LOG_FILE


def setup_logging() -> None:
    """Configure the logging module.

    Uses ``trading_intel.config.LOG_FILE`` for the log file path if set.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        filename=LOG_FILE if LOG_FILE else None,
    )
