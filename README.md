# Robo-Advisor

A portfolio optimization application that builds and backtests investment portfolios using Modern Portfolio Theory. The project consists of a C++ core engine for numerical optimization, a Python FastAPI backend, and a Next.js frontend dashboard.

## Architecture

* **C++ Core (`cpp_core/`)**: Calculates mean-variance optimization and backtesting performance using the Eigen matrix library.
* **FastAPI Backend (`backend/`)**: Handles market data ingestion from Yahoo Finance, risk profile evaluation, and API endpoints. Includes a Python fallback if the C++ module is not compiled.
* **Next.js Frontend (`frontend/`)**: Web dashboard for completing risk questionnaires and viewing portfolio allocation and historical metrics.

## How to Run

### Option 1: Docker (Recommended)

To build and run both the backend and frontend in Docker containers:

```bash
docker-compose up --build
```

Access points:
* Frontend: http://localhost:3000
* Backend API Docs: http://localhost:8000/docs

### Option 2: Running Locally

If you prefer to run the components directly on your machine:

1. Start the FastAPI backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

2. Start the Next.js frontend:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser to access the dashboard.
