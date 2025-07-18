#!/usr/bin/env python3
import subprocess, sys, os

def start():
    subprocess.run("(crontab -l 2>/dev/null; echo '@hourly cd ~/trading_intel && python inference.py >> inference.log 2>&1') | crontab -", shell=True)
    print("✅ Scheduled hourly inference (crontab added).")

def stop():
    subprocess.run("crontab -l | grep -v 'inference.py' | crontab -", shell=True)
    print("🛑 Stopped hourly inference.")

def status():
    out = subprocess.run("crontab -l", shell=True, capture_output=True, text=True)
    print("📋 Crontab:\n", out.stdout)

if __name__=="__main__":
    if len(sys.argv)<2:
        print("usage: cli.py [start|stop|status]")
    elif sys.argv[1]=="start":
        start()
    elif sys.argv[1]=="stop":
        stop()
    else:
        status()
