#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# generate-traffic.sh — Normal Traffic Generator
# TicketFlow Event Ticketing Platform — Elastic Observability Lab
#
# Usage:
#   chmod +x scripts/generate-traffic.sh
#   ./scripts/generate-traffic.sh
#
# Simulates normal browsing traffic:
#   - Users browsing event listings
#   - Users checking specific events
#   - Users looking up individual tickets
#
# Stop with: Ctrl+C
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
SLEEP_SECONDS="${SLEEP_SECONDS:-1}"
REQUEST_COUNT=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TicketFlow — Normal Traffic Generator"
echo "  Target: ${BASE_URL}"
echo "  Simulating: browse events, view tickets"
echo "  Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

while true; do
    REQUEST_COUNT=$((REQUEST_COUNT + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[${TIMESTAMP}] Session #${REQUEST_COUNT}"

    # Homepage
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/")
    echo "  GET /                     → HTTP ${STATUS}"

    # Health check
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")
    echo "  GET /health               → HTTP ${STATUS}"

    # Browse all events (the page most users land on)
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/events")
    echo "  GET /api/events           → HTTP ${STATUS}  [event listing]"

    # View individual event pages
    for EVENT_ID in 1 2 3; do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/events/${EVENT_ID}")
        echo "  GET /api/events/${EVENT_ID}       → HTTP ${STATUS}  [event detail]"
    done

    # Look up individual tickets
    for TICKET_ID in 101 102 104; do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/tickets/${TICKET_ID}")
        echo "  GET /api/tickets/${TICKET_ID}     → HTTP ${STATUS}  [ticket lookup]"
    done

    echo ""
    sleep "${SLEEP_SECONDS}"
done
