#!/usr/bin/env python3
"""
generate-traffic.py — Cross-platform Normal Traffic Generator
"""
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
SLEEP_SECONDS = float(os.getenv("SLEEP_SECONDS", "1"))

print("=" * 50)
print("  TicketFlow — Normal Traffic Generator (Python)")
print(f"  Target: {BASE_URL}")
print("  Press Ctrl+C to stop")
print("=" * 50 + "\n")

def fetch(path):
    url = f"{BASE_URL}{path}"
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TicketFlow-TrafficGen/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed = (time.perf_counter() - start) * 1000
            return resp.status, round(elapsed, 1)
    except urllib.error.HTTPError as e:
        elapsed = (time.perf_counter() - start) * 1000
        return e.code, round(elapsed, 1)
    except Exception as e:
        return f"ERR ({e})", 0

count = 0
try:
    while True:
        count += 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] Session #{count}")
        
        status, ms = fetch("/")
        print(f"  GET /                     -> HTTP {status} [{ms}ms]")
        
        status, ms = fetch("/health")
        print(f"  GET /health               -> HTTP {status} [{ms}ms]")
        
        status, ms = fetch("/api/events")
        print(f"  GET /api/events           -> HTTP {status} [{ms}ms]")
        
        for eid in [1, 2, 3]:
            status, ms = fetch(f"/api/events/{eid}")
            print(f"  GET /api/events/{eid}       -> HTTP {status} [{ms}ms]")
            
        for tid in [101, 102, 104]:
            status, ms = fetch(f"/api/tickets/{tid}")
            print(f"  GET /api/tickets/{tid}     -> HTTP {status} [{ms}ms]")
            
        print()
        time.sleep(SLEEP_SECONDS)
except KeyboardInterrupt:
    print("\nStopped.")
