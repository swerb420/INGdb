#!/usr/bin/env python3
import subprocess, sys, os, logging
from config import LOG_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename=LOG_FILE if LOG_FILE else None,
)
logger = logging.getLogger(__name__)

def start():
    subprocess.run(
        "(crontab -l 2>/dev/null; echo '@hourly cd ~/trading_intel && python inference.py >> inference.log 2>&1') | crontab -",
        shell=True,
    )
    logger.info("\u2705 Scheduled hourly inference (crontab added).")

def stop():
    subprocess.run("crontab -l | grep -v 'inference.py' | crontab -", shell=True)
    logger.info("\U0001F6D1 Stopped hourly inference.")

def status():
    out = subprocess.run("crontab -l", shell=True, capture_output=True, text=True)
    logger.info("\U0001F4CB Crontab:\n%s", out.stdout)

if __name__=="__main__":
    if len(sys.argv)<2:
        logger.error("usage: cli.py [start|stop|status]")
    elif sys.argv[1]=="start":
        start(sys.argv[2] if len(sys.argv) > 2 else None)
    elif sys.argv[1]=="stop":
        stop()
    else:
        status()
