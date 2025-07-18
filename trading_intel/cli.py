#!/usr/bin/env python3
import subprocess, sys, shutil
from config import PROJECT_DIR

def _check_cron():
    if not shutil.which("crontab"):
        raise EnvironmentError("'crontab' command not found. Is cron installed?")

def start(path=None):
    _check_cron()
    path = path or PROJECT_DIR
    current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    cron = current.stdout if current.returncode == 0 else ""
    entry = f"@hourly cd {path} && python inference.py >> inference.log 2>&1"
    if entry not in cron:
        if cron and not cron.endswith("\n"):
            cron += "\n"
        cron += entry + "\n"
    subprocess.run(["crontab", "-"], input=cron, text=True, check=True)
    print("✅ Scheduled hourly inference (crontab added).")

def stop():
    _check_cron()
    current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    cron = current.stdout if current.returncode == 0 else ""
    new_cron = "\n".join(
        line for line in cron.splitlines() if "inference.py" not in line
    )
    subprocess.run(["crontab", "-"], input=new_cron + "\n", text=True, check=True)
    print("🛑 Stopped hourly inference.")

def status():
    _check_cron()
    out = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=True)
    print("📋 Crontab:\n", out.stdout)

if __name__=="__main__":
    if len(sys.argv)<2:
        print("usage: cli.py [start|stop|status] [path]")
    elif sys.argv[1]=="start":
        start(sys.argv[2] if len(sys.argv) > 2 else None)
    elif sys.argv[1]=="stop":
        stop()
    else:
        status()
