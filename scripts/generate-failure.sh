#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# generate-failure.sh — Incident Traffic Generator
# TicketFlow Event Ticketing Platform — Elastic Observability Lab
#
# Usage:
#   Step 1: Enable the seat-inventory latency simulation
#     Edit .env → SIMULATE_LATENCY=true
#     docker compose up -d --force-recreate app
#
#   Step 2: Run this script to generate incident telemetry
#     chmod +x scripts/generate-failure.sh
#     ./scripts/generate-failure.sh
#
# What it simulates:
#   Users hitting "Browse Events" while the seat-inventory API is slow.
#   Each request to /api/events takes 2-5 seconds instead of <200ms.
#   This is a realistic incident: an external dependency degrading under load.
#
# What to look for in Kibana:
#   APM → Services → ticketflow-api → Latency spike on GET /api/events
#   APM → Traces   → inventory.sync span consuming 2-5s
#   Discover → logs-otel-demo* → WARNING: slow seat inventory sync detected
#
# Stop with: Ctrl+C
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
SLEEP_SECONDS="${SLEEP_SECONDS:-1}"
REQUEST_COUNT=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TicketFlow — INCIDENT SCENARIO"
echo "  Simulating: slow seat-inventory API"
echo "  Target: ${BASE_URL}/api/events"
echo ""
echo "  ⚠  Make sure SIMULATE_LATENCY=true is set:"
echo "     1. Edit .env → SIMULATE_LATENCY=true"
echo "     2. docker compose up -d --force-recreate app"
echo ""
echo "  Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Safety check: verify latency simulation is active
echo "Verifying incident mode is active..."
RESPONSE=$(curl -s "${BASE_URL}/health" 2>/dev/null || echo '{"simulate_latency":"unknown"}')
SIMULATE=$(echo "${RESPONSE}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('simulate_latency','unknown'))" 2>/dev/null || echo "unknown")

if [ "${SIMULATE}" = "False" ] || [ "${SIMULATE}" = "false" ]; then
    echo ""
    echo "⚠  WARNING: simulate_latency is currently DISABLED"
    echo "   The incident scenario will not be visible in Kibana."
    echo ""
    echo "   To enable:"
    echo "     1. Edit .env → SIMULATE_LATENCY=true"
    echo "     2. docker compose up -d --force-recreate app"
    echo ""
    read -rp "Continue anyway? (y/N): " CONFIRM
    if [ "${CONFIRM}" != "y" ] && [ "${CONFIRM}" != "Y" ]; then
        echo "Aborted."
        exit 0
    fi
elif [ "${SIMULATE}" = "True" ] || [ "${SIMULATE}" = "true" ]; then
    echo "✓ Incident mode ACTIVE — seat inventory latency enabled"
    echo ""
fi

while true; do
    REQUEST_COUNT=$((REQUEST_COUNT + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    echo -n "[${TIMESTAMP}] Request #${REQUEST_COUNT} → GET /api/events (seat inventory sync) ... "

    START_NS=$(date +%s%N 2>/dev/null || date +%s)
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/events")
    END_NS=$(date +%s%N 2>/dev/null || date +%s)

    if [[ "${START_NS}" =~ [0-9]{13,} ]]; then
        DURATION_MS=$(( (END_NS - START_NS) / 1000000 ))
        echo "HTTP ${STATUS} — ${DURATION_MS}ms"
    else
        echo "HTTP ${STATUS}"
    fi

    sleep "${SLEEP_SECONDS}"
done
