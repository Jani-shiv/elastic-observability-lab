#!/usr/bin/env python3
"""
generate-failure.py — Cross-platform Incident Traffic Generator
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
print("  TicketFlow — INCIDENT SCENARIO (Python)")
print(f"  Target: {BASE_URL}/api/events")
print("  Press Ctrl+C to stop")
print("=" * 50 + "\n")

# Health check
try:
    with urllib.request.urlopen(f"{BASE_URL}/health", timeout=5) as resp:
        import json
        data = json.loads(resp.read().decode())
        if data.get("simulate_latency"):
            print("[+] Incident mode ACTIVE - seat inventory latency enabled (2-5s delays)\n")
        else:
            print("[!] WARNING: simulate_latency is DISABLED on the server.")
            print("  Set SIMULATE_LATENCY=true in .env and restart app container.\n")
except Exception as e:
    print(f"Could not connect to health endpoint: {e}\n")

count = 0
try:
    while True:
        count += 1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] Request #{count} -> GET /api/events ... ", end="", flush=True)
        
        start = time.perf_counter()
        try:
            req = urllib.request.Request(f"{BASE_URL}/api/events", headers={"User-Agent": "TicketFlow-FailureGen/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                elapsed = (time.perf_counter() - start) * 1000
                print(f"HTTP {resp.status} - {elapsed:.1f}ms")
        except urllib.error.HTTPError as e:
            elapsed = (time.perf_counter() - start) * 1000
            print(f"HTTP {e.code} - {elapsed:.1f}ms")
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            print(f"FAILED ({e}) — {elapsed:.1f}ms")
            
        time.sleep(SLEEP_SECONDS)
except KeyboardInterrupt:
    print("\nStopped.")
