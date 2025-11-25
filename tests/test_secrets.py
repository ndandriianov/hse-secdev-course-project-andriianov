import os
from importlib import reload

from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


def test_secret_key_is_loaded_from_env():
    os.environ["SECRET_KEY"] = "custom-test-secret-xyz"

    import src.app.auth

    reload(src.app.auth)

    from src.app import SECRET_KEY

    assert SECRET_KEY == "custom-test-secret-xyz"


def test_default_secret_is_used_when_not_set(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    import src.app.auth

    reload(src.app.auth)

    from src.app import SECRET_KEY

    assert SECRET_KEY == "CHANGE_THIS_SECRET_IN_DEVELOPMENT"


def test_secret_key_leak_in_response():
    signup = client.post("/signup", json={"username": "leaktest", "password": "pass"})
    token = signup.json()["access_token"]

    response = client.get("/objectives", headers={"Authorization": f"Bearer {token}"})

    assert "SECRET_KEY" not in response.text
    assert "CHANGE_THIS_SECRET_IN_DEVELOPMENT" not in response.text
    assert os.environ.get("SECRET_KEY", "") not in response.text
