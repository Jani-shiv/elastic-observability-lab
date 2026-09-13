# Elastic Observability Lab V1 — Task Checklist

## Definition of Done

### Application
- [ ] FastAPI application runs locally
- [ ] `GET /` works and returns service info
- [ ] `GET /health` returns `{"status": "healthy"}`
- [ ] `GET /api/orders` returns order list
- [ ] `GET /api/orders/{order_id}` returns single order
- [ ] Application logs are structured JSON
- [ ] Every request emits a log with endpoint, status, duration_ms
- [ ] Slow requests (>1000ms) emit a WARNING log

### OpenTelemetry
- [ ] OTel SDK initialised on startup
- [ ] FastAPI auto-instrumented (HTTP spans)
- [ ] Custom spans: `orders.list`, `orders.get`, `order.processing`
- [ ] Span attributes set: route, order_id, simulate_latency, artificial_delay_s
- [ ] Metrics collected: `http_requests_total`, `http_request_duration_ms`
- [ ] Python logging bridged to OTel (logs have trace_id)
- [ ] OTLP gRPC exporter configured

### Infrastructure
- [ ] `app/Dockerfile` builds successfully
- [ ] `docker compose up -d` starts all 4 services
- [ ] All containers show `healthy` status
- [ ] Elasticsearch accessible at `http://localhost:9200`
- [ ] Kibana accessible at `http://localhost:5601`
- [ ] OTel Collector receives telemetry (visible in collector logs)
- [ ] Telemetry reaches Elasticsearch (indices created)

### Observability Demo
- [ ] Normal traffic can be generated (`./scripts/generate-traffic.sh`)
- [ ] Traces visible in Kibana APM
- [ ] Metrics visible in Kibana APM
- [ ] Logs visible in Kibana Discover
- [ ] `SIMULATE_LATENCY=true` introduces 2–5s delay
- [ ] Latency increase is visible in APM
- [ ] Slow `order.processing` span is visible in trace waterfall
- [ ] `artificial_delay_s` attribute visible in span
- [ ] WARNING log visible in Discover during incident
- [ ] Application recovers after `SIMULATE_LATENCY=false`
- [ ] Latency returns to normal baseline after recovery

### Evidence & Documentation
- [ ] Kibana screenshots captured (01–06)
- [ ] `docs/incident-report.md` complete
- [ ] `README.md` complete with architecture diagram
- [ ] Quick Start commands work for a fresh clone
- [ ] `.env.example` is safe to commit (no secrets)
- [ ] `.gitignore` excludes `.env`, data volumes, credentials
- [ ] No secrets committed to Git
- [ ] Repository can be reproduced by another developer

### Git Hygiene
- [ ] Commits use meaningful messages (`feat:`, `docs:`)
- [ ] `screenshots/.gitkeep` keeps the screenshots directory tracked
- [ ] Docker volumes excluded from Git
