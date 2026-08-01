# Robo-Advisor — Quantitative Portfolio Engine & Infrastructure Platform

[![CI Pipeline](https://github.com/blais/roboadvisor/actions/workflows/ci.yml/badge.svg)](https://github.com/blais/roboadvisor/actions)
![Terraform](https://img.shields.io/badge/Terraform-1.5+-7B42BC.svg)
![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C.svg)
![C++17](https://img.shields.io/badge/C%2B%2B-17-blue.svg)
![Python 3.11](https://img.shields.io/badge/Python-3.11-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)
![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

An end-to-end quantitative portfolio advisory platform & infrastructure showcase. Features a native **C++ optimization engine** (Eigen matrix math via pybind11), a **FastAPI backend** with PostgreSQL persistence, **Prometheus telemetry & health probes**, **Locust load testing**, **Terraform Infrastructure as Code (AWS)**, and an interactive **Next.js dashboard**.

---

## 🏗 Infrastructure & System Architecture

```
                               ┌────────────────────────────────────────┐
                               │           Prometheus / Grafana         │
                               │  P95/P99 Latency, RPS, C++ Solves      │
                               └───────────────────▲────────────────────┘
                                                   │ Scrape /metrics
┌──────────────────┐  HTTP    ┌────────────────────┴───────────────────┐  PostgreSQL   ┌──────────────┐
│  Client / Load   ├─────────►│           FastAPI Gateway              ├──────────────►│ Amazon RDS   │
│  (Locust / k6)   │          │ • Rate Limiter    • Telemetry Timing   │               │ PostgreSQL   │
└──────────────────┘          │ • Health Probes   • C++ Native Core    │               └──────────────┘
                              └────────────────────┬───────────────────┘
                                                   │
                               ┌───────────────────▼───────────────────┐
                               │          Terraform IaC (AWS)          │
                               │  VPC, ECS Fargate, RDS, S3, IAM Roles │
                               └───────────────────────────────────────┘
```

---

## ⚡ Quantitative & Latency Performance Benchmark

The engine solves for the **Tangency Portfolio** (Maximizing Sharpe Ratio) by solving regularized linear systems $\boldsymbol{\Sigma}_{reg} \mathbf{x} = (\boldsymbol{\mu} - r_f \mathbf{1})$. Native C++ execution is timed via Prometheus histograms.

| Asset Dimension ($N$) | C++ Eigen Engine Latency | Python SciPy Latency | Speedup Factor | Throughput (C++) |
| :---: | :---: | :---: | :---: | :---: |
| **4 Assets** | **0.0076 ms** | 0.9634 ms | **127.6x Faster** | ~132,400 ops/sec |
| **10 Assets** | **0.0163 ms** | 2.1466 ms | **132.0x Faster** | ~61,400 ops/sec |

---

## 📊 Observability & Telemetry (`/metrics`)

The FastAPI service exports Prometheus metrics for observability and SLA tracking:

* **`http_requests_total`**: Counter of HTTP requests partitioned by `method`, `endpoint`, and `status_code`.
* **`http_request_duration_seconds`**: Latency histogram tracking $P50$, $P95$, and $P99$ response times.
* **`cpp_optimizer_duration_seconds`**: High-precision timer measuring C++ solver execution time.

### Health & Resilience Probes
* **`GET /health/live`**: Liveness probe for Kubernetes / ECS task orchestrators.
* **`GET /health/ready`**: Readiness probe executing database ping (`SELECT 1`).

---

## ☁️ Infrastructure as Code (Terraform)

Declarative cloud infrastructure defined in `terraform/`:

* **Networking**: AWS VPC with 2 public & 2 private subnets across multiple Availability Zones.
* **Compute**: AWS ECS Fargate cluster for containerized task execution.
* **Database**: AWS RDS PostgreSQL instance in private database subnets with security groups.
* **Storage & IAM**: S3 Bucket for static assets & data caching with least-privilege IAM roles.

### Provisioning Infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

---

## 🧮 Mathematical Foundations

### 1. Tangency Portfolio (Maximum Sharpe Ratio)
$$\max_{\mathbf{w}} \frac{\mathbf{w}^T \boldsymbol{\mu} - r_f}{\sqrt{\mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w}}} \quad \text{s.t.} \quad \sum_{i=1}^N w_i = 1$$

To avoid explicit matrix inversion instability, the core solves:
$$\boldsymbol{\Sigma}_{reg} \mathbf{u} = (\boldsymbol{\mu} - r_f \mathbf{1}), \quad \mathbf{w} = \frac{\mathbf{u}}{\mathbf{1}^T \mathbf{u}}$$

### 2. Covariance Shrinkage & Regularization
$$\boldsymbol{\Sigma}_{reg} = \boldsymbol{\Sigma} + \epsilon \mathbf{I}, \quad \epsilon = 10^{-6}$$

---

## 📁 Project Layout

```
.
├── backend/
│   ├── main.py              # FastAPI endpoints, Prometheus metrics & health probes
│   ├── ingest_data.py       # Yahoo Finance market data ingestion & local caching
│   ├── database.py          # SQLAlchemy engine & session factory
│   ├── models.py            # ORM models (User, RiskProfile, Portfolio)
│   └── test_main.py         # Pytest API test suite
├── cpp_core/
│   ├── Optimizer.h/cpp      # Eigen-based matrix math & regularization
│   ├── Backtester.h/cpp     # CAGR, Sharpe ratio, and Max Drawdown calculation
│   ├── Bindings.cpp         # Pybind11 zero-copy wrapper
│   └── test_optimizer.cpp   # Standalone C++ unit test runner
├── terraform/
│   ├── main.tf              # AWS VPC, ECS Fargate, RDS PostgreSQL, S3 resources
│   ├── variables.tf         # Input variable definitions
│   └── outputs.tf           # Resource endpoint outputs
├── load_tests/
│   └── locustfile.py        # Locust load & capacity testing scenario
├── frontend/                # Next.js 14 Web Dashboard
├── docker-compose.yml       # Containerized multi-service orchestration
└── .github/workflows/ci.yml # GitHub Actions CI pipeline
```

---

## 🚀 Running locally & Load Testing

### Run App via Docker Compose
```bash
docker compose up --build
```

### Run Pytest Suite
```bash
pytest backend/test_main.py
```

### Run Headless Locust Load Test
```bash
locust -f load_tests/locustfile.py --headless -u 20 -r 5 --run-time 10s --host http://localhost:8000
```

---

## 🛡 License
Distributed under the MIT License. See `LICENSE` for details.
