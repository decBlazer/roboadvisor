from locust import HttpUser, task, between
import random

class RoboAdvisorUser(HttpUser):
    wait_time = between(1, 2.5)

    @task(3)
    def test_risk_profile(self):
        payload = {
            "age": random.randint(22, 65),
            "investment_timeline_years": random.randint(3, 20),
            "loss_tolerance": random.choice(["low", "medium", "high"]),
            "email": f"locust_user_{random.randint(1, 1000)}@example.com"
        }
        self.client.post("/risk-profile", json=payload, name="/risk-profile")

    @task(5)
    def test_allocate_portfolio(self):
        payload = {
            "tier": random.choice(["Conservative", "Moderate", "Growth", "Aggressive"]),
            "tickers": ["SPY", "QQQ", "TLT", "GLD"],
            "email": f"locust_user_{random.randint(1, 1000)}@example.com"
        }
        self.client.post("/allocate", json=payload, name="/allocate")

    @task(2)
    def test_backtest(self):
        payload = {
            "tickers": ["SPY", "TLT"],
            "weights": [0.6, 0.4],
            "start_date": "2022-01-01",
            "end_date": "2023-01-01"
        }
        self.client.post("/backtest", json=payload, name="/backtest")

    @task(4)
    def test_rebalance_check(self):
        payload = {
            "current_holdings": {"SPY": 0.70, "TLT": 0.30},
            "target_holdings": {"SPY": 0.60, "TLT": 0.40},
            "threshold": 0.05,
            "email": f"locust_user_{random.randint(1, 1000)}@example.com"
        }
        self.client.post("/rebalance-check", json=payload, name="/rebalance-check")

    @task(1)
    def test_health_and_metrics(self):
        self.client.get("/health/ready", name="/health/ready")
        self.client.get("/metrics", name="/metrics")
