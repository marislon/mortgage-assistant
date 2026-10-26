from fastapi.testclient import TestClient

from app.main import app
from app.routers import payment_day


def test_repeated_decision_returns_409(monkeypatch):
    def fake_get_application_status(application_id):
        return "completed"

    monkeypatch.setattr(
        payment_day,
        "get_application_status",
        fake_get_application_status,
    )

    client = TestClient(app)

    response = client.post(
        "/applications/26/decision",
        json={"decision": "approved"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Заявление не ожидает решения сотрудника"
    )
