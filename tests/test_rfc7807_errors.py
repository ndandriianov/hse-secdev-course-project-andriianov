from fastapi.testclient import TestClient

from src import app

client = TestClient(app)


def test_validation_error_rfc7807_format():
    signup = client.post("/signup", json={"username": "test", "password": "pass"})
    token = signup.json()["access_token"]

    response = client.post(
        "/objectives",
        json={"title": "a", "period_name": "bad"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["type"] == "https://api.okr.example.com/probs/validation-error"
    assert data["title"] == "Unprocessable Entity"
    assert data["status"] == 422
    assert "errors" in data


def test_successful_response_not_rfc7807():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "type" not in data
