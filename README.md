# Elastic Observability Lab

> A self-contained local lab demonstrating end-to-end application observability using
> **FastAPI**, **OpenTelemetry**, and **Elastic Observability** — from a healthy baseline
> through an intentional performance incident to root-cause investigation and recovery.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![Elastic Stack](https://img.shields.io/badge/Elastic-8.17-005571.svg)](https://elastic.co)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-1.29-f5a623.svg)](https://opentelemetry.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

This project builds a complete, reproducible observability demo that answers a real question:

> **When an application slows down, how do you find out why — fast?**

The answer: correlated **logs + metrics + traces** flowing through OpenTelemetry into Elastic Observability.

The demo follows a complete investigation workflow:

```
Application running normally
        ↓
Intentional latency introduced (SIMULATE_LATENCY=true)
        ↓
Elastic detects the change
        ↓
Investigate metrics → identify the affected endpoint
        ↓
Inspect traces → find the slow span
        ↓
Check logs → confirm root cause
        ↓
Fix → verify recovery
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Compose Network                      │
│                                                                   │
│   ┌───────────────┐   OTLP gRPC    ┌────────────────────┐       │
│   │  FastAPI App  │ ─────────────► │  OTel Collector    │       │
│   │  :8000        │                │  (contrib:0.115.0) │       │
│   │               │                │  :4317 gRPC        │       │
│   │  Endpoints:   │                │  :4318 HTTP        │       │
│   │  /health      │                └─────────┬──────────┘       │
│   │  /api/orders  │                          │                   │
│   │  /api/orders/ │                          │ Elasticsearch     │
│   │  {order_id}   │                          │ HTTP API          │
│   └───────────────┘                          ▼                   │
│                                   ┌─────────────────────┐       │
│                                   │   Elasticsearch     │       │
│                                   │   8.17.0 :9200      │       │
│                                   │                      │       │
│                                   │  traces-otel-demo   │       │
│                                   │  metrics-otel-demo  │       │
│                                   │  logs-otel-demo     │       │
│                                   └──────────┬──────────┘       │
│                                              │                   │
│                                              ▼                   │
│                                   ┌─────────────────────┐       │
│                                   │      Kibana          │       │
│                                   │   8.17.0 :5601       │       │
│                                   │                      │       │
│                                   │  APM → Traces        │       │
│                                   │  Discover → Logs     │       │
│                                   │  Dashboards → Metrics│       │
│                                   └─────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## What This Demonstrates

| Concept | How it's shown |
|---|---|
| **Structured logging** | JSON logs emitted per-request with duration, endpoint, status |
| **Distributed tracing** | OTel spans: HTTP layer → `orders.list` → `order.processing` |
| **Application metrics** | `http_requests_total` counter, `http_request_duration_ms` histogram |
| **OTel instrumentation** | FastAPI auto-instrumented via `opentelemetry-instrumentation-fastapi` |
| **Telemetry pipeline** | OTLP → OTel Collector → Elasticsearch (3 separate pipelines) |
| **Incident simulation** | `SIMULATE_LATENCY=true` introduces 2–5s delay with WARNING log |
| **Root-cause investigation** | Correlated traces + logs identify the slow span without source code |
| **Recovery verification** | Metrics return to baseline after disabling latency |

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Application | Python / FastAPI / Uvicorn | 3.12 / 0.115 / 0.32 |
| Instrumentation | OpenTelemetry Python SDK | 1.29.0 |
| Telemetry pipeline | OTel Collector (contrib) | 0.115.0 |
| Search & storage | Elasticsearch | 8.17.0 |
| Visualisation | Kibana | 8.17.0 |
| Container runtime | Docker + Docker Compose | — |

---

## Project Structure

```
elastic-observability-lab/
│
├── app/
│   ├── main.py               # FastAPI app — endpoints, logging, OTel setup
│   ├── requirements.txt      # Pinned Python dependencies
│   └── Dockerfile            # Non-root, health-checked container
│
├── docs/
│   └── incident-report.md    # Full incident investigation report
│
├── elastic/
│   └── otel-config.yml       # OTel Collector: receivers, processors, exporters
│
├── scripts/
│   ├── generate-traffic.sh   # Normal baseline traffic generator
│   └── generate-failure.sh   # Incident traffic generator
│
├── screenshots/              # Kibana evidence (captured during demo)
│
├── docker-compose.yml        # Full 4-service stack definition
├── .env.example              # Environment variable template (safe to commit)
├── .gitignore
├── LICENSE
├── README.md
└── TASK.md                   # V1 definition-of-done checklist
```

---

## Prerequisites

| Requirement | Minimum version | Notes |
|---|---|---|
| Docker Desktop | 4.x | Enable WSL 2 backend on Windows |
| Docker Compose | v2 | Included in Docker Desktop |
| `curl` | any | For health checks and traffic generation |
| `bash` | 4+ | For the generator scripts (Git Bash / WSL on Windows) |
| RAM | 4 GB available | Elasticsearch needs ~1 GB heap |

> **Windows users:** Run the shell scripts in Git Bash, WSL, or any POSIX-compatible shell.

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/<your-username>/elastic-observability-lab.git
cd elastic-observability-lab

cp .env.example .env
```

The default `.env` values work out-of-the-box for local development (security disabled, no passwords required).

### 2. Start the stack

```bash
docker compose up -d
```

Docker will build the FastAPI image and pull Elasticsearch, Kibana, and the OTel Collector.
First run takes 2–5 minutes depending on your connection.

### 3. Wait for services to be ready

```bash
# Check all 4 containers
docker compose ps

# Watch health status until all show "healthy"
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

Elasticsearch takes ~40 seconds. Kibana takes ~60 seconds.

### 4. Verify the application

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status": "healthy", "service": "elastic-observability-demo", "simulate_latency": false}
```

```bash
curl http://localhost:8000/api/orders
```

### 5. Open Kibana

```
http://localhost:5601
```

Navigate to: **Observability → APM → Services**

After generating traffic (next section), you will see `elastic-observability-demo` listed.

---

## Generate Traffic

Run the normal traffic generator to build a baseline:

```bash
chmod +x scripts/generate-traffic.sh
./scripts/generate-traffic.sh
```

This continuously hits all endpoints every second. Let it run for 2–3 minutes to populate Kibana.

---

## Simulate the Incident

### Step 1 — Enable latency

Edit `.env`:

```bash
SIMULATE_LATENCY=true
```

Restart only the app container (keep Elasticsearch and Kibana running):

```bash
docker compose up -d --force-recreate app
```

Verify latency is active:

```bash
curl http://localhost:8000/health
# → "simulate_latency": true
```

### Step 2 — Generate failure traffic

```bash
chmod +x scripts/generate-failure.sh
./scripts/generate-failure.sh
```

Each request to `/api/orders` will now take 2–5 seconds. Let it run for 2–3 minutes.

---

## Investigate in Kibana

### Traces

```
Observability → APM → Services → elastic-observability-demo → Transactions
```

- Look for `GET /api/orders` — the average latency will be 3–5× higher than normal
- Click into a sample trace to see the waterfall
- The `order.processing` span will consume most of the duration
- Span attributes will show `artificial_delay_s` and `simulate_latency: true`

### Logs

```
Discover → Index pattern: logs-otel-demo*
```

- Filter: `level: WARNING`
- Look for `"message": "slow order processing detected"`
- The `duration_ms` field will show values of 2,000–5,000ms
- The `alert: LATENCY_SPIKE` field confirms the condition

### Metrics

```
Observability → APM → Services → elastic-observability-demo → Overview
```

- The throughput and latency charts will show a clear before/after pattern
- The `http_request_duration_ms` histogram shows the distribution shift

---

## Root Cause

The investigation reveals:

| Signal | Evidence |
|---|---|
| **Metric** | `http_request_duration_ms` P99 > 4,000ms on `/api/orders` |
| **Trace** | `order.processing` span duration 2,000–5,000ms; attribute `artificial_delay_s` present |
| **Log** | `WARNING: slow order processing detected` with `simulate_latency: true` |

**Root cause:** `SIMULATE_LATENCY=true` activated a `time.sleep(2–5s)` call inside `order.processing`,
simulating a slow downstream dependency.

### Recovery

```bash
# In .env, set:
SIMULATE_LATENCY=false

# Restart app
docker compose up -d --force-recreate app

# Verify
curl http://localhost:8000/health
# → "simulate_latency": false

# Resume normal traffic
./scripts/generate-traffic.sh
```

Latency returns to the 50–200ms baseline within seconds.

---

## Screenshots

| # | File | Description |
|---|---|---|
| 1 | `screenshots/01-normal-traffic.png` | APM service overview — healthy baseline |
| 2 | `screenshots/02-latency-spike.png` | Latency increase on `/api/orders` |
| 3 | `screenshots/03-affected-endpoint.png` | Transaction list showing affected endpoint |
| 4 | `screenshots/04-slow-trace.png` | Trace waterfall with slow `order.processing` span |
| 5 | `screenshots/05-application-log.png` | WARNING log with `slow order processing detected` |
| 6 | `screenshots/06-root-cause.png` | Span attributes showing `artificial_delay_s` |

> Screenshots are captured during the live demo and saved to `screenshots/`.

---

## What I Learned

1. **Observability is about correlation.** A single signal (metric, log, or trace) rarely tells the full story. The combination makes root-cause analysis possible without reading code.

2. **OpenTelemetry abstracts the vendor.** The application emits standard OTLP. Switching from Elastic to another backend is a configuration change, not an application change.

3. **Structured JSON logs are worth the setup.** Freeform logs make filtering slow and error-prone. JSON logs with consistent fields (`endpoint`, `duration_ms`, `status_code`) make Kibana queries trivial.

4. **Trace attributes are evidence.** Adding `artificial_delay_s`, `simulate_latency`, and `order.id` as span attributes meant the investigation could be completed in Kibana without ever looking at source code.

5. **Docker Compose health checks matter.** Without proper `depends_on` + `condition: service_healthy`, the app container starts before Elasticsearch is ready, causing connection failures.

---

## Future Improvements (V2)

- [ ] Kubernetes deployment (Helm charts)
- [ ] Prometheus integration for metrics scraping
- [ ] Real PostgreSQL dependency with slow query simulation
- [ ] Redis cache dependency
- [ ] Multiple microservices with service-to-service tracing
- [ ] Kibana alerting rules on latency SLOs
- [ ] Anomaly detection with Elastic ML
- [ ] Elastic AI Assistant for automated incident investigation
- [ ] Agentic root-cause analysis

---

## Teardown

```bash
# Stop all containers
docker compose down

# Remove volumes (deletes Elasticsearch data)
docker compose down -v
```

---

## License

MIT — see [LICENSE](LICENSE).
