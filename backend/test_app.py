import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "models" in data

def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "ap_valid" in data
    assert "ap_test" in data
    assert "p_at_k" in data

def test_bundle_info():
    response = client.get("/bundle/info")
    assert response.status_code == 200
    data = response.json()
    assert "extract_dir" in data
    assert "num_models" in data

def test_meta():
    response = client.get("/meta")
    assert response.status_code == 200
    data = response.json()
    assert "card" in data

def test_equity():
    response = client.get("/equity?k=50")
    assert response.status_code == 200
    data = response.json()
    assert "dates" in data
    assert "equity" in data
    assert len(data["dates"]) == len(data["equity"])
