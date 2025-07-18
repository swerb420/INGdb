#!/usr/bin/env python3
import logging
import subprocess
import sys
from pathlib import Path

from typing import List, Optional

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


def main(argv: Optional[List[str]] = None) -> int:
    """Dispatch CLI commands."""
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("usage: ti-cli [start|stop|status]", file=sys.stderr)
        return 1

    cmd = argv[0]
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
