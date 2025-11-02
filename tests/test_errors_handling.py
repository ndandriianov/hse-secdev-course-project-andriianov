from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_unhandled_exception_returns_rfc7807_and_correlation_id():
    @app.get("/_test_unhandled_exception")
    def _raise_unhandled():
        raise ValueError("Something went wrong!")

    resp = client.get("/_test_unhandled_exception")
    assert resp.status_code == 500

    body = resp.json()

    assert "type" in body
    assert "title" in body
    assert "status" in body
    assert "detail" in body
    assert "correlation_id" in body

    assert body["status"] == 500
    assert isinstance(body["correlation_id"], str)
    assert "Something went wrong" not in body["detail"]
