import logging
import time
import uuid
from collections import defaultdict
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="SecDev Course App", version="0.1.0")

logger = logging.getLogger("secdev_app")
logger.setLevel(logging.INFO)

response_times = []


def mask_secret(value: str) -> str:
    if not value:
        return value
    if len(value) > 8:
        return value[:4] + "*" * (len(value) - 4)
    return "****"


@app.middleware("http")
async def response_time_middleware(request: Request, call_next):
    """Middleware для измерения времени отклика и установки correlation_id."""
    start_time = time.time()

    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled error (correlation_id=%s): %s", correlation_id, exc)
        return JSONResponse(
            status_code=500,
            content={
                "type": "about:blank",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An internal error occurred. Contact support with correlation_id",
                "correlation_id": correlation_id,
            },
        )

    process_time = time.time() - start_time
    process_time_ms = round(process_time * 1000, 2)

    response_times.append(
        {
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "response_time_ms": process_time_ms,
            "timestamp": time.time(),
            "correlation_id": correlation_id,
        }
    )

    response.headers["X-Response-Time"] = f"{process_time_ms}ms"
    response.headers["X-Correlation-ID"] = correlation_id

    return response


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        correlation_id: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.status = status
        self.correlation_id = correlation_id


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    correlation_id = (
        getattr(request.state, "correlation_id", None)
        or exc.correlation_id
        or str(uuid.uuid4())
    )
    safe_message = mask_secret(exc.message)
    logger.info(
        "ApiError handled (correlation_id=%s): code=%s message=%s",
        correlation_id,
        exc.code,
        safe_message,
    )
    return JSONResponse(
        status_code=exc.status,
        content={
            "type": "about:blank",
            "title": exc.code.replace("_", " ").title(),
            "status": exc.status,
            "detail": exc.message,  # сюда оставляем полное сообщение для клиента
            "correlation_id": correlation_id,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    correlation_id = getattr(request.state, "correlation_id", None) or str(uuid.uuid4())
    logger.info(
        "HTTPException (correlation_id=%s): status=%s detail=%s",
        correlation_id,
        exc.status_code,
        exc.detail,
    )
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": "Http Error",
            "status": exc.status_code,
            "detail": detail,
            "correlation_id": correlation_id,
        },
    )


RATE_LIMIT_STORE: Dict[str, List[float]] = defaultdict(list)
MAX_REQUESTS = 5
TIME_WINDOW_SECONDS = 60


def get_client_ip(request: Request) -> str:
    """Получает IP-адрес клиента для простого Rate Limiting."""
    return request.client.host if request.client else "unknown"


def rate_limit_dependency(request: Request):
    """Зависимость FastAPI для проверки лимита запросов."""
    ip = get_client_ip(request)
    current_time = time.time()

    window_start = current_time - TIME_WINDOW_SECONDS
    RATE_LIMIT_STORE[ip] = [t for t in RATE_LIMIT_STORE[ip] if t >= window_start]

    if len(RATE_LIMIT_STORE[ip]) >= MAX_REQUESTS:
        time_to_wait = int(
            TIME_WINDOW_SECONDS - (current_time - RATE_LIMIT_STORE[ip][0])
        )
        correlation_id = getattr(request.state, "correlation_id", None)
        raise ApiError(
            code="rate_limit",
            message=f"Too many requests. Try again in {time_to_wait} seconds.",
            status=429,
            correlation_id=correlation_id,
        )

    RATE_LIMIT_STORE[ip].append(current_time)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def get_metrics():
    """Эндпоинт для получения метрик времени отклика"""
    if not response_times:
        return {"message": "Нет данных о времени отклика"}

    times = [rt["response_time_ms"] for rt in response_times]

    avg_time = round(sum(times) / len(times), 2)
    max_time = max(times)
    min_time = min(times)

    status_counts = {}
    for rt in response_times:
        status = rt["status_code"]
        status_counts[status] = status_counts.get(status, 0) + 1

    endpoint_counts = {}
    for rt in response_times:
        endpoint = f"{rt['method']} {rt['path']}"
        endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

    return {
        "total_requests": len(response_times),
        "response_time_stats": {
            "avg_ms": avg_time,
            "max_ms": max_time,
            "min_ms": min_time,
            "requests_over_200ms": len([t for t in times if t > 200]),
        },
        "status_codes": status_counts,
        "endpoints": endpoint_counts,
        "recent_requests": response_times[-10:],
    }


# Example minimal entity (for tests/demo)
_DB = {"items": []}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)
