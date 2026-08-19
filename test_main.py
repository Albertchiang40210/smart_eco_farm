import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_receive_sensor_data():
    payload = {
        "device_id": "test_sensor_1",
        "temperature": 25.5,
        "humidity": 70.0,
        "soil_moisture": 45.0
    }
    response = client.post("/api/v1/sensors", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "alert" in data

def test_get_sensor_history():
    response = client.get("/api/v1/sensors/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
