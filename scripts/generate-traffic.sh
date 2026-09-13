#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# generate-traffic.sh — Normal Traffic Generator
# Elastic Observability Lab
#
# Usage:
#   chmod +x scripts/generate-traffic.sh
#   ./scripts/generate-traffic.sh
#
# What it does:
#   Continuously sends requests to all application endpoints.
#   Generates a steady baseline of telemetry for comparison during incidents.
#
# Stop with: Ctrl+C
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
SLEEP_SECONDS="${SLEEP_SECONDS:-1}"
REQUEST_COUNT=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Elastic Observability Lab — Traffic Generator"
echo "  Target: ${BASE_URL}"
echo "  Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

while true; do
    REQUEST_COUNT=$((REQUEST_COUNT + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[${TIMESTAMP}] Request #${REQUEST_COUNT}"

    # Root endpoint
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/")
    echo "  GET /               → HTTP ${STATUS}"

    # Health check
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
    echo "  GET /health         → HTTP ${STATUS}"

    # List all orders
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/orders")
    echo "  GET /api/orders     → HTTP ${STATUS}"

    # Individual orders
    for ORDER_ID in 1 2 3; do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/orders/${ORDER_ID}")
        echo "  GET /api/orders/${ORDER_ID} → HTTP ${STATUS}"
    done

    echo ""
    sleep "${SLEEP_SECONDS}"
done
