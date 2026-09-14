"""
TicketFlow — Event Ticketing Platform API
==========================================
Observability demo application instrumented with OpenTelemetry → Elastic.

Simulates a real-world ticketing platform (concerts, sports, theatre).
The slow operation mimics a call to an external seat-inventory service —
a classic real-world latency bottleneck.

Endpoints:
    GET /                              → service info
    GET /health                        → health check
    GET /api/events                    → list upcoming events  ⚠ slow when SIMULATE_LATENCY=true
    GET /api/events/{event_id}         → event details + ticket availability
    GET /api/tickets/{ticket_id}       → individual ticket lookup

Failure scenario:
    SIMULATE_LATENCY=true  →  seat inventory sync takes 2-5s (simulates slow external API)
    SIMULATE_LATENCY=false →  normal operation ~50-200ms
"""

import json
import logging
import os
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

# ─── OpenTelemetry Setup ────────────────────────────────────────────────────
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# ─── Configuration ───────────────────────────────────────────────────────────
SERVICE_NAME_VAL = os.getenv("OTEL_SERVICE_NAME", "ticketflow-api")
SIMULATE_LATENCY = os.getenv("SIMULATE_LATENCY", "false").lower() == "true"
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")

# ─── Structured JSON Logger ──────────────────────────────────────────────────
class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON for Kibana Discover."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME_VAL,
            "logger": record.name,
            "message": record.getMessage(),
        }
        skip = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in skip:
                log_obj[key] = value
        return json.dumps(log_obj)


def setup_logging() -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)
    return logging.getLogger("ticketflow")


logger = setup_logging()


# ─── OpenTelemetry Initialisation ────────────────────────────────────────────
def setup_otel() -> None:
    resource = Resource.create({SERVICE_NAME: SERVICE_NAME_VAL})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=OTLP_ENDPOINT, insecure=True),
        export_interval_millis=10_000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    LoggingInstrumentor().instrument(set_logging_format=False)

    logger.info(
        "TicketFlow API started",
        extra={"otel_endpoint": OTLP_ENDPOINT, "simulate_latency": SIMULATE_LATENCY},
    )


# ─── OTel Instruments ────────────────────────────────────────────────────────
tracer = trace.get_tracer(__name__)
meter  = metrics.get_meter(__name__)

request_counter = meter.create_counter(
    "http_requests_total",
    unit="1",
    description="Total HTTP requests received",
)
request_duration_histogram = meter.create_histogram(
    "http_request_duration_ms",
    unit="ms",
    description="HTTP request duration in milliseconds",
)
ticket_lookup_counter = meter.create_counter(
    "ticket_lookups_total",
    unit="1",
    description="Total ticket/event lookups",
)


# ─── In-Memory Data Store ─────────────────────────────────────────────────────

EVENTS: dict[int, dict] = {
    1: {
        "event_id": 1,
        "name": "Coldplay: Music of the Spheres World Tour",
        "venue": "Wembley Stadium",
        "city": "London, UK",
        "date": "2024-08-15",
        "category": "Concert",
        "available_tickets": 342,
        "total_capacity": 90_000,
        "price_from": 85.00,
        "currency": "GBP",
        "status": "on_sale",
    },
    2: {
        "event_id": 2,
        "name": "UEFA Champions League Final",
        "venue": "Allianz Arena",
        "city": "Munich, Germany",
        "date": "2024-06-01",
        "category": "Sports",
        "available_tickets": 78,
        "total_capacity": 75_000,
        "price_from": 250.00,
        "currency": "EUR",
        "status": "almost_sold_out",
    },
    3: {
        "event_id": 3,
        "name": "Hamilton — The Musical",
        "venue": "Victoria Palace Theatre",
        "city": "London, UK",
        "date": "2024-07-20",
        "category": "Theatre",
        "available_tickets": 15,
        "total_capacity": 1_564,
        "price_from": 55.00,
        "currency": "GBP",
        "status": "almost_sold_out",
    },
    4: {
        "event_id": 4,
        "name": "Taylor Swift: The Eras Tour",
        "venue": "MetLife Stadium",
        "city": "New York, USA",
        "date": "2024-10-12",
        "category": "Concert",
        "available_tickets": 892,
        "total_capacity": 82_500,
        "price_from": 199.00,
        "currency": "USD",
        "status": "on_sale",
    },
    5: {
        "event_id": 5,
        "name": "Formula 1 British Grand Prix",
        "venue": "Silverstone Circuit",
        "city": "Northamptonshire, UK",
        "date": "2024-07-07",
        "category": "Motorsport",
        "available_tickets": 1_205,
        "total_capacity": 150_000,
        "price_from": 120.00,
        "currency": "GBP",
        "status": "on_sale",
    },
    6: {
        "event_id": 6,
        "name": "Wimbledon Men's Final",
        "venue": "All England Club — Centre Court",
        "city": "London, UK",
        "date": "2024-07-14",
        "category": "Sports",
        "available_tickets": 0,
        "total_capacity": 15_000,
        "price_from": 220.00,
        "currency": "GBP",
        "status": "sold_out",
    },
}

TICKETS: dict[int, dict] = {
    101: {"ticket_id": 101, "event_id": 1, "section": "General Admission", "row": None,  "seat": None, "price": 85.00,  "currency": "GBP", "status": "available"},
    102: {"ticket_id": 102, "event_id": 1, "section": "Block A — Premium",  "row": "3",   "seat": "14", "price": 145.00, "currency": "GBP", "status": "available"},
    103: {"ticket_id": 103, "event_id": 2, "section": "North Stand",        "row": "K",   "seat": "22", "price": 250.00, "currency": "EUR", "status": "sold"},
    104: {"ticket_id": 104, "event_id": 3, "section": "Stalls",             "row": "D",   "seat": "7",  "price": 95.00,  "currency": "GBP", "status": "available"},
    105: {"ticket_id": 105, "event_id": 4, "section": "Floor",              "row": None,  "seat": None, "price": 199.00, "currency": "USD", "status": "reserved"},
    106: {"ticket_id": 106, "event_id": 5, "section": "Club Corner",        "row": "G",   "seat": "33", "price": 320.00, "currency": "GBP", "status": "available"},
    107: {"ticket_id": 107, "event_id": 1, "section": "VIP Hospitality",   "row": None,  "seat": None, "price": 850.00, "currency": "GBP", "status": "available"},
    108: {"ticket_id": 108, "event_id": 4, "section": "Pit A",             "row": "2",   "seat": "8",  "price": 499.00, "currency": "USD", "status": "available"},
}


# ─── Seat Inventory Sync ──────────────────────────────────────────────────────
def sync_seat_inventory(event_id: int | None = None) -> tuple[list | dict, float]:
    """
    Synchronise seat inventory from the external ticketing provider.

    In normal operation this is fast (50–200ms).
    When SIMULATE_LATENCY=true this simulates a slow external API call (2–5s),
    representing a real-world bottleneck in the seat-inventory service.
    """
    start = time.perf_counter()

    with tracer.start_as_current_span("inventory.sync") as span:
        span.set_attribute("inventory.event_id", event_id or "all")
        span.set_attribute("inventory.simulate_latency", SIMULATE_LATENCY)

        if SIMULATE_LATENCY:
            # ⚠ Intentional slow path — simulates slow external seat-inventory API
            delay = random.uniform(2.0, 5.0)
            span.set_attribute("inventory.artificial_delay_s", round(delay, 3))
            span.add_event("seat_inventory.request_sent",    {"provider": "TicketMaster-API", "delay_s": round(delay, 3)})
            time.sleep(delay)
            span.add_event("seat_inventory.response_received", {"provider": "TicketMaster-API"})
        else:
            # Normal path: fast in-memory lookup
            time.sleep(random.uniform(0.05, 0.20))

        if event_id is not None:
            if event_id not in EVENTS:
                raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
            # Include ticket details for single event lookup
            event = dict(EVENTS[event_id])
            event_tickets = [t for t in TICKETS.values() if t["event_id"] == event_id]
            event["tickets"] = event_tickets
            result = event
        else:
            result = list(EVENTS.values())

    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, round(elapsed_ms, 2)


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_otel()
    FastAPIInstrumentor.instrument_app(app)
    logger.info(
        "TicketFlow API ready",
        extra={"service": SERVICE_NAME_VAL, "simulate_latency": SIMULATE_LATENCY, "events": len(EVENTS)},
    )
    yield
    logger.info("TicketFlow API shutting down")


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="TicketFlow — Event Ticketing API",
    description=(
        "Event ticketing platform API instrumented with OpenTelemetry → Elastic Observability. "
        "Set SIMULATE_LATENCY=true to trigger the seat-inventory latency scenario."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allows browser UI to call the API) ──────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve the Minecraft web UI at /ui ─────────────────────────────────────
import os as _os
_static_dir = _os.path.join(_os.path.dirname(__file__), "static")
if _os.path.isdir(_static_dir):
    app.mount("/ui", StaticFiles(directory=_static_dir, html=True), name="static")


# ─── Middleware: Request Logging ──────────────────────────────────────────────
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    labels = {
        "endpoint": request.url.path,
        "method": request.method,
        "status_code": str(response.status_code),
    }
    request_counter.add(1, labels)
    request_duration_histogram.record(duration_ms, labels)

    level = logging.WARNING if duration_ms > 1000 else logging.INFO
    log_msg = "slow request detected" if duration_ms > 1000 else "request completed"

    logger.log(
        level,
        log_msg,
        extra={
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


# ─── Routes ──────────────────────────────────────────────────────────────────
@app.get("/", tags=["info"])
async def root():
    """TicketFlow service information."""
    return {
        "service": SERVICE_NAME_VAL,
        "description": "Event Ticketing Platform API",
        "version": "1.0.0",
        "status": "running",
        "simulate_latency": SIMULATE_LATENCY,
        "docs": "/docs",
        "endpoints": {
            "events":  "/api/events",
            "event":   "/api/events/{event_id}",
            "ticket":  "/api/tickets/{ticket_id}",
            "health":  "/health",
        },
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check — always 200 when the service is up."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME_VAL,
        "simulate_latency": SIMULATE_LATENCY,
        "uptime": "ok",
    }


@app.get("/api/events", tags=["events"])
async def list_events():
    """
    List all upcoming events with seat availability.

    Calls the seat-inventory service to get real-time availability counts.

    ⚠ When SIMULATE_LATENCY=true, the inventory sync takes 2–5 seconds,
    simulating a slow external ticketing API — a realistic production bottleneck.
    """
    with tracer.start_as_current_span("events.list") as span:
        span.set_attribute("http.route", "/api/events")

        events, sync_time_ms = sync_seat_inventory()

        total_available = sum(e["available_tickets"] for e in events)
        ticket_lookup_counter.add(len(events), {"operation": "list_events"})

        if SIMULATE_LATENCY:
            logger.warning(
                "slow seat inventory sync detected",
                extra={
                    "endpoint": "/api/events",
                    "operation": "inventory.sync",
                    "duration_ms": sync_time_ms,
                    "simulate_latency": True,
                    "alert": "INVENTORY_LATENCY_SPIKE",
                    "provider": "TicketMaster-API",
                },
            )
        else:
            logger.info(
                "events listed successfully",
                extra={
                    "endpoint": "/api/events",
                    "event_count": len(events),
                    "total_available_tickets": total_available,
                    "sync_time_ms": sync_time_ms,
                },
            )

        return {
            "events": events,
            "count": len(events),
            "total_available_tickets": total_available,
            "inventory_sync_ms": sync_time_ms,
        }


@app.get("/api/events/{event_id}", tags=["events"])
async def get_event(event_id: int):
    """
    Get event details including real-time ticket availability.
    Returns event info plus all associated tickets (available, sold, reserved).
    """
    with tracer.start_as_current_span("events.get") as span:
        span.set_attribute("http.route", "/api/events/{event_id}")
        span.set_attribute("event.id", event_id)

        event, sync_time_ms = sync_seat_inventory(event_id=event_id)

        ticket_lookup_counter.add(1, {"operation": "get_event"})

        logger.info(
            "event retrieved",
            extra={
                "endpoint": f"/api/events/{event_id}",
                "event_id": event_id,
                "event_name": event["name"],
                "available_tickets": event["available_tickets"],
                "sync_time_ms": sync_time_ms,
            },
        )

        return {
            **event,
            "inventory_sync_ms": sync_time_ms,
        }


@app.get("/api/tickets/{ticket_id}", tags=["tickets"])
async def get_ticket(ticket_id: int):
    """Look up a specific ticket by ID."""
    with tracer.start_as_current_span("tickets.get") as span:
        span.set_attribute("http.route", "/api/tickets/{ticket_id}")
        span.set_attribute("ticket.id", ticket_id)

        if ticket_id not in TICKETS:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

        ticket = dict(TICKETS[ticket_id])
        event  = EVENTS.get(ticket["event_id"], {})

        # Fast lookup — no inventory sync needed for individual tickets
        time.sleep(random.uniform(0.02, 0.08))

        ticket_lookup_counter.add(1, {"operation": "get_ticket"})

        logger.info(
            "ticket retrieved",
            extra={
                "endpoint": f"/api/tickets/{ticket_id}",
                "ticket_id": ticket_id,
                "event_id": ticket["event_id"],
                "ticket_status": ticket["status"],
            },
        )

        return {
            **ticket,
            "event_name": event.get("name", "Unknown"),
            "event_date": event.get("date"),
            "venue": event.get("venue"),
        }


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
