#!/usr/bin/env python3
import logging
import subprocess
import sys
from pathlib import Path

from .logging_utils import setup_logging

logger = logging.getLogger(__name__)


def start() -> None:
    project_dir = Path(__file__).resolve().parent
    cmd = (
        "(crontab -l 2>/dev/null; echo '@hourly cd "
        f"{project_dir} && {sys.executable} -m trading_intel.inference "
        ">> inference.log 2>&1') | crontab -"
    )
    subprocess.run(cmd, shell=True)
    logger.info("\u2705 Scheduled hourly inference (crontab added).")


def stop() -> None:
    cmd = "crontab -l | grep -v 'trading_intel.inference' | crontab -"
    subprocess.run(cmd, shell=True)
    logger.info("\U0001f6d1 Stopped hourly inference.")


def status() -> None:
    out = subprocess.run(
        "crontab -l",
        shell=True,
        capture_output=True,
        text=True,
    )
    logger.info("\U0001f4cb Crontab:\n%s", out.stdout)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the command line interface."""
    setup_logging()
    args = sys.argv[1:] if argv is None else argv
    if not args:
        logger.error("usage: cli.py [start|stop|status]")
        return 1
    cmd = args[0]
    if cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "status":
        status()
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
