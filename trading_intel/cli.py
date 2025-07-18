#!/usr/bin/env python3
import logging
import subprocess
import sys
from pathlib import Path

from .config import LOG_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename=LOG_FILE if LOG_FILE else None,
)
logger = logging.getLogger(__name__)


def start():
    project_dir = Path(__file__).resolve().parent
    cmd = (
        "(crontab -l 2>/dev/null; echo '@hourly cd "
        f"{project_dir} && {sys.executable} inference.py "
        ">> inference.log 2>&1') | crontab -"
    )
    subprocess.run(cmd, shell=True)
    logger.info("\u2705 Scheduled hourly inference (crontab added).")


def stop():
    cmd = "crontab -l | grep -v 'inference.py' | crontab -"
    subprocess.run(cmd, shell=True)
    logger.info("\U0001f6d1 Stopped hourly inference.")


def status():
    out = subprocess.run(
        "crontab -l",
        shell=True,
        capture_output=True,
        text=True,
    )
    logger.info("\U0001f4cb Crontab:\n%s", out.stdout)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("usage: cli.py [start|stop|status]")
    elif sys.argv[1] == "start":
        start(sys.argv[2] if len(sys.argv) > 2 else None)
    elif sys.argv[1] == "stop":
        stop()
    else:
        status()
