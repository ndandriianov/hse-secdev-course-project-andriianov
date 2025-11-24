from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_not_found_item():
    r = client.get("/items/999")
    assert r.status_code == 404
    body = r.json()

    assert body["status"] == 404
    assert body["title"] == "Not Found"
    assert body["detail"] == "item not found"
    assert body["type"] == "about:blank"
    assert "correlation_id" in body


def test_validation_error():
    r = client.post("/items", params={"name": ""})
    assert r.status_code == 422
    body = r.json()
    assert body["title"] == "Validation Error"
    assert body["detail"] == "name must be 1..100 chars"
