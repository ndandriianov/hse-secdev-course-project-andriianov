import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="SecDev Course App", version="0.1.0")

response_times = []


@app.middleware("http")
async def response_time_middleware(request: Request, call_next):
    """Middleware для измерения времени отклика"""
    start_time = time.time()
    
    response = await call_next(request)
    process_time = time.time() - start_time
    process_time_ms = round(process_time * 1000, 2)
    
    response_times.append({
        "path": request.url.path,
        "method": request.method,
        "status_code": response.status_code,
        "response_time_ms": process_time_ms,
        "timestamp": time.time()
    })
    
    response.headers["X-Response-Time"] = f"{process_time_ms}ms"
    
    return response


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Normalize FastAPI HTTPException into our error envelope
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


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
            "requests_over_200ms": len([t for t in times if t > 200])
        },
        "status_codes": status_counts,
        "endpoints": endpoint_counts,
        "recent_requests": response_times[-10:]
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
