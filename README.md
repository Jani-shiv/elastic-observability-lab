<div align="center">

# ⚡ Elastic Observability Lab — TicketFlow

> **Full-stack Application Observability Platform with OpenTelemetry, FastAPI & Elastic Stack**
> 
> *Detect, diagnose, and resolve artificial seat-inventory microservice latency incidents in real time.*

[![GitHub Stars](https://img.shields.io/github/stars/Jani-shiv/elastic-observability-lab?style=for-the-badge&logo=github&color=1a73e8)](https://github.com/Jani-shiv/elastic-observability-lab/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Jani-shiv/elastic-observability-lab?style=for-the-badge&logo=github&color=34a853)](https://github.com/Jani-shiv/elastic-observability-lab/network/members)
[![License: MIT](https://img.shields.io/badge/License-MIT-fbbc04.svg?style=for-the-badge)](LICENSE)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Elastic Stack](https://img.shields.io/badge/Elastic--Stack-8.19-005571.svg?logo=elasticsearch&logoColor=white)](https://elastic.co)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-0.160-f5a623.svg?logo=opentelemetry&logoColor=white)](https://opentelemetry.io)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)](https://docs.docker.com)

</div>

---

## 📌 Table of Contents
- [📖 Overview](#-overview)
- [🎨 Live Web UI — Google Material Bento Box](#-live-web-ui--google-material-bento-box)
- [🏗️ System Architecture](#️-system-architecture)
- [⚡ Quick Start Guide](#-quick-start-guide)
- [🧪 Traffic & Failure Incident Simulation](#-traffic--failure-incident-simulation)
- [🔍 Kibana Root-Cause Investigation](#-kibana-root-cause-investigation)
- [⭐ Star History](#-star-history)
- [📜 License](#-license)

---

## 📖 Overview

When an enterprise application experiences sudden latency spikes, **how quickly can you pin down the exact root cause?**

This repository provides a production-grade, self-contained **Elastic Observability Lab** instrumented with **OpenTelemetry (OTel)**. It models **TicketFlow**, a modern event ticketing microservice (concerts, sports, theatre). 

The platform emits correlated telemetry across the **Three Pillars of Observability**:
1. **Structured JSON Logs** → Formatted per-request with duration, HTTP status code, and span context.
2. **Distributed Tracing (OTLP)** → End-to-end trace waterfalls detailing external seat-inventory sync spans.
3. **Application Metrics** → Request throughput counters (`http_requests_total`) and latency histograms (`http_request_duration_ms`).

---

## 🎨 Live Web UI — Google Material Bento Box

The frontend features a clean **Google Material Bento Box UI** built with vanilla HTML/CSS/JS and served directly via FastAPI (`/ui`).

```
http://localhost:8000/ui/     ← 🎮 Interactive TicketFlow UI
http://localhost:8000/docs    ← 📖 Swagger API Documentation
http://localhost:5601         ← 🔍 Kibana Observability & APM
```

### Key UI Features
- ⚪ **Google Material White Design**: Crisp typography, Google primary color accents, and elevation cards.
- 🍱 **Bento Box Grid Layout**: Hero banner, live response latency gauge (`inventory_sync_ms`), and ticket availability counters.
- 🚨 **Dynamic Incident Alert**: Top warning banner triggers automatically when `SIMULATE_LATENCY=true` is set.
- 🔍 **Real-Time Filters**: Instant event search by artist, venue, or city with category pills.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Docker Compose Stack Network                        │
│                                                                             │
│   ┌───────────────────────────┐ OTLP gRPC  ┌────────────────────────────┐   │
│   │   FastAPI TicketFlow App  │ ─────────► │   OTel Collector           │   │
│   │   :8000                   │   :4317    │   (contrib:0.160.0)        │   │
│   │   Endpoints:              │            │   - receivers: [otlp]      │   │
│   │     /health               │            │   - exporters: [elasticsearch]│
│   │     /api/events           │            └─────────────┬──────────────┘   │
│   │     /api/tickets/{id}     │                          │                  │
│   └───────────────────────────┘                          │ OTLP Export      │
│                                                          ▼                  │
│                                            ┌────────────────────────────┐   │
│                                            │  Elasticsearch 8.19        │   │
│                                            │  :9200                     │   │
│                                            │  - traces-otel-demo        │   │
│                                            │  - metrics-otel-demo       │   │
│                                            │  - logs-otel-demo          │   │
│                                            └─────────────┬──────────────┘   │
│                                                          │                  │
│                                                          ▼                  │
│                                            ┌────────────────────────────┐   │
│                                            │  Kibana 8.19               │   │
│                                            │  :5601                     │   │
│                                            │  - APM Traces & Spans      │   │
│                                            │  - Structured Discover     │   │
│                                            └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start Guide

### 1. Clone & Configure
```bash
git clone https://github.com/Jani-shiv/elastic-observability-lab.git
cd elastic-observability-lab

# Create local environment config
cp .env.example .env
```

### 2. Launch Stack with Docker Compose
```bash
docker compose up -d --build
```

### 3. Check Health Status
```bash
# Verify containers are running healthy
docker compose ps

# Check API health endpoint
curl http://localhost:8000/health
```

---

## 🧪 Traffic & Failure Incident Simulation

We provide cross-platform scripts for **Windows PowerShell**, **Python**, and **Linux Bash**.

### 🟢 1. Normal Baseline Traffic
Run the normal traffic generator to create healthy baseline telemetry:

```powershell
# Windows PowerShell
.\scripts\generate-traffic.ps1

# Cross-Platform Python
python scripts/generate-traffic.py

# Linux / Mac Bash
./scripts/generate-traffic.sh
```

---

### 🔴 2. Simulate Latency Incident
To test an intentional performance bottleneck (simulates slow 2–5s seat-inventory API response):

1. **Enable Latency in `.env`**:
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

   # Linux / Mac Bash
   ./scripts/generate-failure.sh
   ```

---

## 🔍 Kibana Root-Cause Investigation

Navigate to Kibana at `http://localhost:5601` to inspect the incident telemetry:

| Telemetry Signal | Kibana Navigation | Evidence Found |
|---|---|---|
| 📊 **Metrics** | `APM → Services → ticketflow-api` | Latency spike on `GET /api/events` (P99 jumps from 150ms to 4500ms) |
| 🪟 **Traces** | `APM → Traces → inventory.sync` | Trace waterfall pinpoints `inventory.sync` span consuming 2.5s - 5.0s |
| 📝 **Logs** | `Discover → logs-otel-demo*` | `WARNING: slow request detected` with `duration_ms: 3840` |

---

## ⭐ Star History

If you find this lab helpful for learning Elastic Observability and OpenTelemetry, give it a star on GitHub!

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=Jani-shiv/elastic-observability-lab&type=Date)](https://star-history.com/#Jani-shiv/elastic-observability-lab&Date)

</div>

---

## 📜 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
