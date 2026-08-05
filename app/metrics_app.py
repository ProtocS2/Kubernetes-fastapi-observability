from fastapi import FastAPI, Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time

app = FastAPI()

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path", "status_code"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5]
)

IN_FLIGHT = Gauge(
    "http_requests_in_flight",
    "Number of HTTP requests currently being processed"
)

SUCCESSFUL_LOGINS = Counter(
    "successful_logins_total",
    "Total successful logins"
)

FAILED_LOGINS = Counter(
    "failed_logins_total",
    "Total failed logins"
)

ITEMS_PROCESSED = Counter(
    "items_processed_total",
    "Total items processed"
)

@app.middleware("http")
async def collect_http_metrics(request: Request, call_next):
    IN_FLIGHT.inc()
    start = time.perf_counter()
    response = None
    status_code = "500"

    try:
        response = await call_next(request)
        status_code = str(response.status_code)
        return response
    finally:
        duration = time.perf_counter() - start

        REQUEST_COUNT.labels(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
        ).observe(duration)

        IN_FLIGHT.dec()

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/login/success")
def login_success():
    SUCCESSFUL_LOGINS.inc()
    return {"message": "login successful"}

@app.post("/login/fail")
def login_fail():
    FAILED_LOGINS.inc()
    return {"message": "login failed"}

@app.post("/items/process")
def process_item():
    ITEMS_PROCESSED.inc()
    return {"message": "item processed"}
