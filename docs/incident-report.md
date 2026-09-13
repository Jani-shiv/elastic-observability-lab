# Incident Report

**Service:** `elastic-observability-demo`
**Date:** 2024-01-15
**Severity:** P2 — Degraded Performance
**Status:** Resolved

---

## Incident

The `/api/orders` endpoint experienced a significant and sustained increase in response latency,
rising from a normal baseline of 50–200ms to 2,000–5,000ms per request.

---

## Impact

| Dimension     | Detail                                         |
|---------------|------------------------------------------------|
| **Endpoint**  | `GET /api/orders`                              |
| **Duration**  | ~10 minutes (demo scenario)                    |
| **Severity**  | Degraded performance — requests slow, not failing |
| **Users**     | All consumers of the Orders API                |
| **HTTP codes**| 200 (requests succeeded but were very slow)    |

Requests returned successfully but with unacceptable latency, causing poor user experience.

---

## Detection

Kibana APM showed a clear latency spike on the `elastic-observability-demo` service.

The `http_request_duration_ms` metric increased from the normal baseline (~100ms) to peaks
of 4,000–5,000ms, crossing the visible threshold in the APM latency histogram.

**Detection signal:** Metric — `http_request_duration_ms` on `/api/orders`

---

## Investigation

### Step 1 — Detect

The APM service overview showed elevated latency on `elastic-observability-demo`.
Average response time increased from ~130ms to ~3,500ms.

### Step 2 — Confirm

Filtered the APM transaction view to confirm only `/api/orders` was affected.
`GET /health` and `GET /api/orders/{order_id}` remained at normal latency.

**Finding:** The degradation was isolated to a single endpoint.

### Step 3 — Investigate Traces

Opened a sample trace for a slow `/api/orders` request in Kibana APM.

The trace waterfall showed:

```
GET /api/orders                        4,218ms total
  └─ orders.list                       4,215ms
       └─ order.processing             4,210ms   ← SLOW SPAN
            └─ artificial_delay.start
            └─ artificial_delay.end
```

The `order.processing` span consumed nearly the entire request duration.
The span attribute `artificial_delay_s: 4.21` was visible.

### Step 4 — Correlate with Logs

Searched Kibana Discover for `logs-otel-demo*` filtered to `level: WARNING`.

Found repeated log entries:

```json
{
  "timestamp": "2024-01-15T10:23:41.521Z",
  "level": "WARNING",
  "service": "elastic-observability-demo",
  "message": "slow order processing detected",
  "endpoint": "/api/orders",
  "duration_ms": 4218.5,
  "simulate_latency": true,
  "alert": "LATENCY_SPIKE"
}
```

The `simulate_latency: true` attribute in the log confirmed the source.

### Step 5 — Identify Root Cause

The combination of:
- Trace: slow `order.processing` span with `artificial_delay_s` attribute
- Log: `WARNING` with `simulate_latency: true` field

...made the root cause unambiguous without needing to read the application source code.

---

## Root Cause

The `SIMULATE_LATENCY` environment variable was set to `true`, activating an artificial
delay of 2–5 seconds in the `simulate_order_processing()` function.

This simulates a slow downstream dependency (e.g., a slow database query, a slow external API call,
or an unoptimised background operation).

**Root cause:** `SIMULATE_LATENCY=true` → artificial `time.sleep(2–5s)` in order processing.

---

## Resolution

1. Set `SIMULATE_LATENCY=false` in `.env`
2. Restarted the application container:
   ```bash
   docker compose up -d --force-recreate app
   ```
3. Ran `./scripts/generate-traffic.sh` to verify recovery.

---

## Verification

After resolution:

| Metric                    | Before (incident) | After (resolution) |
|---------------------------|-------------------|--------------------|
| Avg response time         | ~3,500ms          | ~130ms             |
| P99 response time         | ~5,000ms          | ~200ms             |
| WARNING logs/min          | ~60               | 0                  |
| `order.processing` span   | 2,000–5,000ms     | 50–200ms           |

Kibana APM latency chart returned to the normal baseline within 2 minutes of restart.

---

## Lessons Learned

### What worked well

1. **Traces** pinpointed the exact slow operation (`order.processing` span) within seconds.
2. **Logs** provided supporting context (`simulate_latency: true`) that confirmed the root cause.
3. **Metrics** (`http_request_duration_ms`) provided the first alerting signal.
4. **Correlation** — the three signals told a coherent story without requiring source code access.

### Key insight

> Logs, metrics, and traces are each incomplete on their own.
> A metric tells you *something is wrong*.
> A trace tells you *where it's slow*.
> A log tells you *why it happened*.
> Together they reduce mean-time-to-resolution significantly.

### What to improve

- Add alerting rules in Kibana when `http_request_duration_ms` P99 exceeds 1,000ms
- Add SLO tracking for the `/api/orders` endpoint
- Consider tracing the artificial delay as a separate child span to make it even more visible

---

## References

- [Elastic APM Documentation](https://www.elastic.co/guide/en/observability/current/apm.html)
- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/languages/python/)
- [OTel Collector Elasticsearch Exporter](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/elasticsearchexporter)
