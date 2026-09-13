"""
Elastic Observability Lab — FastAPI Demo Application
=====================================================
Demonstrates OpenTelemetry instrumentation with Elastic Observability.

Endpoints:
    GET /              → root info
    GET /health        → health check
    GET /api/orders    → list orders (supports SIMULATE_LATENCY)
    GET /api/orders/{order_id} → single order

Environment Variables:
    SIMULATE_LATENCY      → "true" enables artificial 2–5s delay on /api/orders
    OTEL_SERVICE_NAME     → service name (default: elastic-observability-demo)
    OTEL_EXPORTER_OTLP_ENDPOINT → OTel Collector endpoint
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
from fastapi.responses import JSONResponse

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
SERVICE_NAME_VAL = os.getenv("OTEL_SERVICE_NAME", "elastic-observability-demo")
SIMULATE_LATENCY = os.getenv("SIMULATE_LATENCY", "false").lower() == "true"
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")

# ─── Structured JSON Logger ──────────────────────────────────────────────────
class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON for easy parsing in Kibana."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME_VAL,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge any extra fields passed via `extra=`
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            ):
                log_obj[key] = value
        return json.dumps(log_obj)


def setup_logging() -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    return logging.getLogger("app")


logger = setup_logging()


# ─── OpenTelemetry Initialisation ────────────────────────────────────────────
def setup_otel() -> None:
    resource = Resource.create({SERVICE_NAME: SERVICE_NAME_VAL})

    # Tracer
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    # Meter
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=OTLP_ENDPOINT, insecure=True),
        export_interval_millis=10_000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Bridge Python logging → OTel
    LoggingInstrumentor().instrument(set_logging_format=False)

    logger.info(
        "OpenTelemetry initialised",
        extra={
            "otel_endpoint": OTLP_ENDPOINT,
            "simulate_latency": SIMULATE_LATENCY,
        },
    )


# ─── OTel Instruments ────────────────────────────────────────────────────────
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

request_counter = meter.create_counter(
    "http_requests_total",
    unit="1",
    description="Total number of HTTP requests",
)
request_duration_histogram = meter.create_histogram(
    "http_request_duration_ms",
    unit="ms",
    description="HTTP request duration in milliseconds",
)


# ─── In-Memory Order Store ────────────────────────────────────────────────────
ORDERS: dict[int, dict] = {
    1: {"order_id": 1, "customer": "Alice", "item": "Laptop",    "quantity": 1, "status": "completed"},
    2: {"order_id": 2, "customer": "Bob",   "item": "Keyboard",  "quantity": 2, "status": "processing"},
    3: {"order_id": 3, "customer": "Carol", "item": "Monitor",   "quantity": 1, "status": "completed"},
    4: {"order_id": 4, "customer": "Dave",  "item": "Mouse",     "quantity": 3, "status": "shipped"},
    5: {"order_id": 5, "customer": "Eve",   "item": "Headphones","quantity": 1, "status": "completed"},
}


# ─── Helper ───────────────────────────────────────────────────────────────────
def simulate_order_processing(order_id: int | None = None) -> tuple[dict, float]:
    """
    Simulate order processing.
    When SIMULATE_LATENCY is True, inject artificial 2–5 second delay.
    Returns (order_data, processing_time_ms).
    """
    start = time.perf_counter()

    with tracer.start_as_current_span("order.processing") as span:
        span.set_attribute("order.id", order_id or "all")
        span.set_attribute("simulate_latency", SIMULATE_LATENCY)

        if SIMULATE_LATENCY:
            # ⚠ Intentional artificial delay — failure scenario
            delay = random.uniform(2.0, 5.0)
            span.set_attribute("artificial_delay_s", round(delay, 3))
            span.add_event("artificial_delay.start", {"delay_s": round(delay, 3)})
            time.sleep(delay)
            span.add_event("artificial_delay.end")

        else:
            # Normal processing: 50–200 ms
            normal_delay = random.uniform(0.05, 0.20)
            time.sleep(normal_delay)

        if order_id is not None:
            if order_id not in ORDERS:
                raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
            result = dict(ORDERS[order_id])
        else:
            result = list(ORDERS.values())

    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, round(elapsed_ms, 2)


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_otel()
    FastAPIInstrumentor.instrument_app(app)
    logger.info(
        "Application started",
        extra={"service": SERVICE_NAME_VAL, "simulate_latency": SIMULATE_LATENCY},
    )
    yield
    logger.info("Application shutting down")


# ─── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Elastic Observability Demo",
    description="FastAPI demo app instrumented with OpenTelemetry → Elastic Observability",
    version="1.0.0",
    lifespan=lifespan,
)


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
    """Service information endpoint."""
    return {
        "service": SERVICE_NAME_VAL,
        "version": "1.0.0",
        "status": "running",
        "simulate_latency": SIMULATE_LATENCY,
        "docs": "/docs",
        "endpoints": ["/health", "/api/orders", "/api/orders/{order_id}"],
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint. Always returns 200 if the service is up."""
    return {"status": "healthy", "service": SERVICE_NAME_VAL, "simulate_latency": SIMULATE_LATENCY}


@app.get("/api/orders", tags=["orders"])
async def list_orders():
    """
    List all orders.

    ⚠ When SIMULATE_LATENCY=true this endpoint will have 2–5 second response times.
    This is intentional — it simulates a slow downstream dependency.
    """
    with tracer.start_as_current_span("orders.list") as span:
        span.set_attribute("http.route", "/api/orders")

        orders, processing_time_ms = simulate_order_processing()

        if SIMULATE_LATENCY:
            logger.warning(
                "slow order processing detected",
                extra={
                    "endpoint": "/api/orders",
                    "duration_ms": processing_time_ms,
                    "simulate_latency": True,
                    "alert": "LATENCY_SPIKE",
                },
            )
        else:
            logger.info(
                "orders listed successfully",
                extra={"endpoint": "/api/orders", "count": len(orders), "duration_ms": processing_time_ms},
            )

        return {
            "orders": orders,
            "count": len(orders),
            "processing_time_ms": processing_time_ms,
        }


@app.get("/api/orders/{order_id}", tags=["orders"])
async def get_order(order_id: int):
    """Retrieve a single order by ID."""
    with tracer.start_as_current_span("orders.get") as span:
        span.set_attribute("http.route", "/api/orders/{order_id}")
        span.set_attribute("order.id", order_id)

        order, processing_time_ms = simulate_order_processing(order_id=order_id)

        logger.info(
            "order retrieved",
            extra={
                "endpoint": f"/api/orders/{order_id}",
                "order_id": order_id,
                "duration_ms": processing_time_ms,
            },
        )

        return {
            "order_id": order["order_id"],
            "customer": order["customer"],
            "item": order["item"],
            "quantity": order["quantity"],
            "status": order["status"],
            "processing_time_ms": processing_time_ms,
        }


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
