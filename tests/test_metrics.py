from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_response_time():
    """Тест времени отклика health эндпоинта"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Response-Time" in response.headers

    response_time = response.headers["X-Response-Time"]
    assert response_time.endswith("ms")

    time_ms = float(response_time[:-2])
    assert time_ms < 1000


def test_metrics_endpoint():
    """Тест эндпоинта метрик"""
    client.get("/health")
    client.get("/health")
    client.post("/items", params={"name": "test"})

    response = client.get("/metrics")
    assert response.status_code == 200

    metrics = response.json()
    assert "total_requests" in metrics
    assert "response_time_stats" in metrics
    assert metrics["total_requests"] >= 3

    stats = metrics["response_time_stats"]
    assert "avg_ms" in stats
    assert "max_ms" in stats
    assert "min_ms" in stats
    assert "requests_over_200ms" in stats

    assert stats["avg_ms"] > 0
    assert stats["max_ms"] > 0
    assert stats["min_ms"] > 0


def test_response_time_under_200ms():
    """Тест что большинство запросов выполняются за < 200ms"""
    for _ in range(5):
        client.get("/health")
        client.get("/items/1")

    response = client.get("/metrics")
    metrics = response.json()

    stats = metrics["response_time_stats"]

    assert stats["avg_ms"] < 200
    assert stats["max_ms"] < 200
