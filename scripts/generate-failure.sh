#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# generate-failure.sh — Incident Traffic Generator
# Elastic Observability Lab
#
# Usage:
#   Step 1: Enable latency simulation
#     Edit .env → SIMULATE_LATENCY=true
#     docker compose up -d --force-recreate app
#
#   Step 2: Run this script to generate failure telemetry
#     chmod +x scripts/generate-failure.sh
#     ./scripts/generate-failure.sh
#
# What it does:
#   Hammers /api/orders with continuous requests.
#   Each request will experience 2–5 second artificial latency.
#   This creates enough telemetry for investigation in Kibana.
#
# What to look for in Kibana:
#   - APM → Services → elastic-observability-demo → Latency spike
#   - Discover → logs-otel-demo* → WARNING messages
#   - APM → Traces → Slow spans on /api/orders
#
# Stop with: Ctrl+C
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
SLEEP_SECONDS="${SLEEP_SECONDS:-1}"
REQUEST_COUNT=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Elastic Observability Lab — FAILURE SCENARIO"
echo "  Target: ${BASE_URL}/api/orders"
echo ""
echo "  ⚠ Make sure SIMULATE_LATENCY=true before running!"
echo "    docker compose up -d --force-recreate app"
echo ""
echo "  Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verify latency is enabled before hammering
echo "Checking if latency simulation is active..."
RESPONSE=$(curl -s "${BASE_URL}/health")
SIMULATE=$(echo "${RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('simulate_latency','unknown'))" 2>/dev/null || echo "unknown")

if [ "${SIMULATE}" = "False" ] || [ "${SIMULATE}" = "false" ]; then
    echo ""
    echo "⚠  WARNING: simulate_latency is currently FALSE"
    echo "   To enable the failure scenario:"
    echo "     1. Edit .env → SIMULATE_LATENCY=true"
    echo "     2. docker compose up -d --force-recreate app"
    echo ""
    read -rp "Continue anyway? (y/N): " CONFIRM
    if [ "${CONFIRM}" != "y" ] && [ "${CONFIRM}" != "Y" ]; then
        echo "Aborted."
        exit 0
    fi
else
    echo "✓ Latency simulation is ACTIVE — proceeding"
fi

echo ""

while true; do
    REQUEST_COUNT=$((REQUEST_COUNT + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    echo -n "[${TIMESTAMP}] Request #${REQUEST_COUNT} → GET /api/orders ... "
    START_TIME=$(date +%s%N 2>/dev/null || date +%s)
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/orders")
    END_TIME=$(date +%s%N 2>/dev/null || date +%s)

    # Calculate duration (nanoseconds → milliseconds if available)
    if [[ "${START_TIME}" =~ [0-9]{13,} ]]; then
        DURATION_MS=$(( (END_TIME - START_TIME) / 1000000 ))
        echo "HTTP ${STATUS} — ${DURATION_MS}ms"
    else
        echo "HTTP ${STATUS}"
    fi

    sleep "${SLEEP_SECONDS}"
done
