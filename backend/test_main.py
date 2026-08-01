import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "cpp_engine_active" in data

def test_prometheus_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text

def test_health_liveness_probe():
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data

def test_health_readiness_probe():
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"

def test_risk_profile_endpoint():
    payload = {
        "age": 25,
        "investment_timeline_years": 10,
        "loss_tolerance": "high",
        "email": "test_user@example.com"
    }
    response = client.post("/risk-profile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "recommended_tier" in data
    assert data["recommended_tier"] in ["Conservative", "Moderate-Conservative", "Moderate", "Growth", "Aggressive"]
    assert data["risk_score"] > 50

def test_allocate_endpoint():
    payload = {
        "tier": "Growth",
        "tickers": ["SPY", "QQQ", "TLT", "GLD"],
        "email": "test_user@example.com"
    }
    response = client.post("/allocate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "optimized_weights" in data
    assert len(data["optimized_weights"]) == 4
    weights_sum = sum(data["optimized_weights"])
    assert pytest.approx(weights_sum, abs=1e-2) == 1.0

def test_backtest_endpoint():
    payload = {
        "tickers": ["SPY", "TLT"],
        "weights": [0.6, 0.4],
        "start_date": "2022-01-01",
        "end_date": "2023-01-01"
    }
    response = client.post("/backtest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "cagr" in data
    assert "sharpe_ratio" in data
    assert "max_drawdown" in data
    assert "portfolio_value_over_time" in data
    assert len(data["portfolio_value_over_time"]) > 0

def test_rebalance_check_endpoint():
    payload = {
        "current_holdings": {"SPY": 0.70, "TLT": 0.30},
        "target_holdings": {"SPY": 0.60, "TLT": 0.40},
        "threshold": 0.05,
        "email": "test_user@example.com"
    }
    response = client.post("/rebalance-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "rebalance_needed" in data
    assert data["rebalance_needed"] is True
    assert "drift_details" in data
    assert data["drift_details"]["SPY"]["drift"] == pytest.approx(0.10, abs=1e-3)
