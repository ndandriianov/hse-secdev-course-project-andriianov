from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_input_validation_and_normalization():
    signup = client.post("/signup", json={"username": "test2", "password": "pass"})
    token = signup.json()["access_token"]

    response = client.post(
        "/objectives",
        json={"title": "  a  ", "period_name": "  Q1 2025  "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_valid_normalized_input():
    signup = client.post("/signup", json={"username": "test3", "password": "pass"})
    token = signup.json()["access_token"]

    response = client.post(
        "/objectives",
        json={"title": "  Run faster  ", "period_name": "  Q1 2025  "},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Run faster"
    assert data["period_name"] == "Q1 2025"
