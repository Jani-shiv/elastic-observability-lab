<div align="center">

<img src="assets/logo.svg" width="130" alt="Elastic Observability Lab Logo" />

# Elastic Observability Lab — TicketFlow

> **Full-Stack Application Observability Platform with OpenTelemetry, FastAPI and Elastic Stack**
> 
> *Detect, diagnose, and resolve microservice performance bottlenecks and artificial latency incidents in real time.*

<br />

[![GitHub Stars](https://img.shields.io/github/stars/Jani-shiv/elastic-observability-lab?style=for-the-badge&logo=github&color=1A73E8)](https://github.com/Jani-shiv/elastic-observability-lab/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Jani-shiv/elastic-observability-lab?style=for-the-badge&logo=github&color=34A853)](https://github.com/Jani-shiv/elastic-observability-lab/network/members)
[![License: MIT](https://img.shields.io/badge/License-MIT-FBBC04?style=for-the-badge)](LICENSE)

<br />

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.19-005571?style=for-the-badge&logo=elasticsearch&logoColor=white)](https://elastic.co)
[![Kibana](https://img.shields.io/badge/Kibana-8.19-E01A59?style=for-the-badge&logo=kibana&logoColor=white)](https://elastic.co)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-0.160-F5A623?style=for-the-badge&logo=opentelemetry&logoColor=white)](https://opentelemetry.io)
[![Docker Compose](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com)
[![Docker Hub](https://img.shields.io/badge/Docker_Hub-jani712%2Felastic--observability--lab-099CEC?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com/r/jani712/elastic-observability-lab)

</div>

---

## Table of Contents
- [Overview](#overview)
- [Live Web UI — Google Material Bento Box](#live-web-ui--google-material-bento-box)
- [System Architecture](#system-architecture)
- [Quick Start Guide](#quick-start-guide)
- [Traffic and Incident Simulation](#traffic-and-incident-simulation)
- [Kibana Root-Cause Investigation](#kibana-root-cause-investigation)
- [Star History](#star-history)
- [License](#license)

---

## Overview

When a distributed microservice application experiences sudden latency degradation, identifying the root cause quickly requires correlated telemetry across logs, metrics, and traces.

This repository provides a self-contained, production-grade **Elastic Observability Lab** instrumented with **OpenTelemetry (OTel)**. It simulates **TicketFlow**, an event ticketing platform (concerts, sports, theatre), with built-in seat-inventory sync latency simulation.

### Telemetry Pillars
- **Structured JSON Logs**: Emitted per-request with latency duration, HTTP status code, and OTel trace context.
- **Distributed Tracing (OTLP)**: Complete trace waterfalls showcasing external seat-inventory sync spans.
- **Application Metrics**: Total HTTP request throughput counters (`http_requests_total`) and duration histograms (`http_request_duration_ms`).

---

## Live Web UI — Google Material Bento Box

The frontend features a clean **Google Material Bento Box UI** served via FastAPI at `/ui`.

```text
http://localhost:8000/ui/     --> Interactive TicketFlow Web UI
http://localhost:8000/docs    --> Swagger API Documentation
http://localhost:5601         --> Kibana Observability and APM
```

### UI Specifications
- **Google White Palette**: Clean background with Google Blue (`#1a73e8`), Red (`#ea4335`), Yellow (`#fbbc04`), and Green (`#34a853`) accents.
- **Bento Box Grid**: Hero section, real-time backend latency gauge (`inventory_sync_ms`), and total available ticket counter.
- **Dynamic Incident Warning**: Alert banner triggers automatically when `SIMULATE_LATENCY=true` is enabled.
- **Instant Search and Filters**: Event search by artist, venue, or city with category pill filters.

---

## System Architecture

```text
+-----------------------------------------------------------------------------+
|                         Docker Compose Stack Network                        |
|                                                                             |
|   +---------------------------+ OTLP gRPC  +----------------------------+   |
|   |   FastAPI TicketFlow App  | ---------> |   OTel Collector           |   |
|   |   :8000                   |   :4317    |   (contrib:0.160.0)        |   |
|   |   Endpoints:              |            |   - receivers: [otlp]      |   |
|   |     /health               |            |   - exporters: [elasticsearch]|
|   |     /api/events           |            +------------+---------------+   |
|   |     /api/tickets/{id}     |                         |                   |
|   +---------------------------+                         | OTLP Export       |
|                                                         v                   |
|                                            +----------------------------+   |
|                                            |  Elasticsearch 8.19        |   |
|                                            |  :9200                     |   |
|                                            |  - traces-otel-demo        |   |
|                                            |  - metrics-otel-demo       |   |
|                                            |  - logs-otel-demo          |   |
|                                            +------------+---------------+   |
|                                                         |                   |
|                                                         v                   |
|                                            +----------------------------+   |
|                                            |  Kibana 8.19               |   |
|                                            |  :5601                     |   |
|                                            |  - APM Traces & Spans      |   |
|                                            |  - Structured Discover     |   |
|                                            +----------------------------+   |
+-----------------------------------------------------------------------------+
```

---

## Quick Start Guide

### 1. Clone and Configure
```bash
git clone https://github.com/Jani-shiv/elastic-observability-lab.git
cd elastic-observability-lab

# Copy environment variables
cp .env.example .env
```

### 2. Launch Docker Stack
```bash
docker compose up -d --build
```

### 3. Check Health Status
```bash
# Check container status
docker compose ps

# Check API health
curl http://localhost:8000/health
```

---

## Traffic and Incident Simulation

We provide cross-platform traffic scripts for **Windows PowerShell**, **Python**, and **Linux Bash**.

### 1. Normal Baseline Traffic
Run the normal traffic generator to populate healthy telemetry baseline:

```powershell
# Windows PowerShell
.\scripts\generate-traffic.ps1

# Cross-Platform Python
python scripts/generate-traffic.py

# Linux / macOS Bash
./scripts/generate-traffic.sh
```

---

### 2. Simulate Latency Incident
To introduce an artificial 2–5 second external seat-inventory sync bottleneck:

1. **Set Latency in `.env`**:
   ```env
   SIMULATE_LATENCY=true
   ```

2. **Recreate App Container**:
   ```bash
   docker compose up -d --force-recreate app
   ```

3. **Run Incident Generator**:
   ```powershell
   # Windows PowerShell
   .\scripts\generate-failure.ps1

   # Cross-Platform Python
   python scripts/generate-failure.py

   # Linux / macOS Bash
   ./scripts/generate-failure.sh
   ```

---

## Kibana Root-Cause Investigation

Access Kibana at `http://localhost:5601` to inspect telemetry:

| Telemetry Signal | Kibana Path | Evidence Found |
|---|---|---|
| **Metrics** | `APM -> Services -> ticketflow-api` | Latency spike on `GET /api/events` (P99 increases from 140ms to 4200ms) |
| **Traces** | `APM -> Traces -> inventory.sync` | Trace waterfall identifies `inventory.sync` span taking 2.5s - 5.0s |
| **Logs** | `Discover -> logs-otel-demo*` | `WARNING: slow request detected` with `duration_ms: 3840` |

---

## Star History

If you find this project helpful for learning Elastic Observability and OpenTelemetry, consider giving it a star on GitHub!

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=Jani-shiv/elastic-observability-lab&type=Date)](https://star-history.com/#Jani-shiv/elastic-observability-lab&Date)

</div>

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
