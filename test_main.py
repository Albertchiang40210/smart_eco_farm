import pytest
from fastapi.testclient import TestClient

from main import app, evaluate_rules
from database import EnvironmentRule

DEVICE = {"X-API-Key": "test-device-key"}
PAYLOAD = {"device_id": "t1", "temperature": 25.5, "humidity": 70.0, "soil_moisture": 45.0}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # 觸發 lifespan → init_db
        yield c


@pytest.fixture(scope="module")
def token(client):
    r = client.post("/api/v1/login", data={"username": "admin", "password": "test-pass"})
    assert r.status_code == 200
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_login_rejects_bad_password(client):
    assert client.post("/api/v1/login", data={"username": "admin", "password": "nope"}).status_code == 400


def test_sensor_requires_api_key(client):
    assert client.post("/api/v1/sensors", json=PAYLOAD).status_code == 401
    assert client.post("/api/v1/sensors", json=PAYLOAD, headers={"X-API-Key": "bad"}).status_code == 401


def test_sensor_rejects_out_of_range(client):
    bad = {**PAYLOAD, "humidity": 500}
    assert client.post("/api/v1/sensors", json=bad, headers=DEVICE).status_code == 422


def test_sensor_ingest_and_history(client, token):
    r = client.post("/api/v1/sensors", json=PAYLOAD, headers=DEVICE)
    assert r.status_code == 200 and r.json()["status"] == "success"

    assert client.get("/api/v1/sensors/history").status_code == 401
    r = client.get("/api/v1/sensors/history", headers=auth(token))
    assert r.status_code == 200
    assert r.json()[0]["temperature"] == 25.5


def test_tasks_history_requires_login(client, token):
    assert client.get("/api/v1/tasks/history").status_code == 401
    assert client.get("/api/v1/tasks/history", headers=auth(token)).status_code == 200


def test_detect_requires_auth(client):
    r = client.post("/api/v1/detect_bugs", files={"file": ("a.jpg", b"x", "image/jpeg")})
    assert r.status_code == 401


def test_detect_rejects_non_image(client):
    r = client.post("/api/v1/detect_bugs", files={"file": ("a.txt", b"x", "text/plain")}, headers=DEVICE)
    assert r.status_code == 415


def _rule(sensor, op, th, target, name):
    return EnvironmentRule(rule_name=name, sensor_type=sensor, condition_operator=op,
                           threshold_value=th, action_target=target, action_command="ON")


def test_rule_engine():
    rules = [_rule("temperature", ">", 28, "fan", "hot"), _rule("humidity", "<", 65, "pump", "dry")]
    d = evaluate_rules(rules, {"temperature": 30, "humidity": 70})
    assert d["fan"][0] == "ON" and d["pump"][0] == "OFF"
    d = evaluate_rules(rules, {"temperature": 20, "humidity": 40})
    assert d["fan"][0] == "OFF" and d["pump"][0] == "ON"
