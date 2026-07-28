Here's the full spec + implementation plan as a markdown doc. Since artifacts aren't available in this chat, it's below in a code block so you can copy it straight into a .md file for Antigravity.

markdown
# Robo-Advisor — Tech Spec & Implementation Plan

## 1. Overview

A robo-advisor that builds and backtests portfolios using Modern Portfolio Theory (MPT).
No AI/LLM dependency — the "intelligence" is deterministic portfolio math (mean-variance
optimization) implemented in C++, exposed to a Python API layer, with a Next.js frontend.

**Goal:** demonstrate quant-finance domain knowledge + systems skills (C++, Python bindings,
API design, frontend) as a fintech-recruiting portfolio piece.

## 2. Architecture

┌─────────────┐ ┌──────────────┐ ┌─────────────────┐
│ Next.js UI │─────▶│ FastAPI │─────▶│ C++ engine │
│ (dashboard) │◀─────│ (Python) │◀─────│ (via pybind11) │
└─────────────┘ └──────┬───────┘ └─────────────────┘
│
┌──────▼───────┐
│ Postgres │
│ (Supabase/ │
│ Railway) │
└───────────────┘


- **C++ core** — performance-critical numerical work only: mean-variance optimization,
  Sharpe ratio maximization, backtesting math (CAGR, Sharpe, max drawdown).
- **Python/FastAPI** — orchestration layer: API endpoints, DB access, calls into the C++
  module via pybind11.
- **Next.js** — risk questionnaire, allocation dashboard, backtest charts.
- **Postgres** — users, risk profiles, portfolios, holdings, rebalance events.

## 3. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Core engine | C++17/20 + Eigen | Matrix ops for covariance, optimization |
| Bindings | pybind11 | Exposes `optimize()`, `backtest()` to Python |
| API | FastAPI (Python) | REST endpoints, orchestration |
| DB | Postgres (Supabase or Railway free tier) | Users, profiles, portfolios |
| Market data | `yfinance` | Free, no API key required |
| Frontend | Next.js | Questionnaire + dashboard |
| Deploy | Docker (backend + compiled C++ lib) on Railway/Render; Vercel (frontend) | |

## 4. C++ engine — module breakdown

- **`Portfolio.h/cpp`** — asset struct, allocation weight vector.
- **`Optimizer.h/cpp`** — mean-variance optimization (Markowitz), Sharpe ratio
  maximization. Use Eigen for covariance matrix construction/inversion. Consider
  Ledoit-Wolf shrinkage for covariance estimation to handle ill-conditioning.
- **`Backtester.h/cpp`** — takes a historical price series + allocation, computes
  CAGR, Sharpe ratio, max drawdown.
- **`Bindings.cpp`** — pybind11 wrapper exposing `optimize()` and `backtest()` as
  Python-callable functions.

## 5. API layer

**Endpoints:**
- `POST /risk-profile` — submit questionnaire, get risk score + preset allocation tier
- `POST /allocate` — given risk profile, return optimized weights (calls C++ optimizer)
- `POST /backtest` — given an allocation, return CAGR/Sharpe/drawdown vs S&P 500 benchmark
- `GET /rebalance-check` — check current holdings against target, flag if drift > 5%

**DB schema (minimum viable):**
- `users` (id, email, created_at)
- `risk_profiles` (user_id, age, timeline, risk_score, tier)
- `portfolios` (id, user_id, target_allocation_json, created_at)
- `holdings` (portfolio_id, asset, weight, last_updated)
- `rebalance_events` (portfolio_id, triggered_at, drift_pct, action_taken)

## 6. Frontend

- Onboarding: risk questionnaire (age, timeline, loss tolerance) → maps to preset tier
- Dashboard:
  - Allocation pie chart (current vs target)
  - Performance line chart (portfolio vs S&P 500, backtested)
  - Rebalance alert banner when drift exceeds threshold

## 7. Risk scoring logic

Weighted score from questionnaire inputs (age, investment timeline, stated loss
tolerance) → maps to one of 5 preset allocation tiers, e.g.:

| Tier | Stock/Bond split |
|---|---|
| Conservative | 30/70 |
| Moderate-conservative | 50/50 |
| Moderate | 70/30 |
| Growth | 80/20 |
| Aggressive | 90/10 |

Each tier's actual weights are then refined via the mean-variance optimizer given
current market covariance data — the preset is a starting point, not the final answer.

## 8. Implementation plan (phased)

### Phase 1 — Foundation
- Repo scaffold: FastAPI backend, Next.js frontend, Postgres (Supabase/Railway)
- DB schema migration
- `yfinance` ingestion script with local caching (avoid rate limits)
- **Deliverable:** API skeleton returns mock portfolio data end-to-end

### Phase 2 — Core allocation engine (C++)
- Eigen-based `Portfolio` struct
- Mean-variance optimizer (efficient frontier, max Sharpe)
- Backtester (CAGR, Sharpe, max drawdown)
- Unit tests for both; benchmark optimizer speed vs a NumPy equivalent
- **Deliverable:** given a risk profile, engine returns optimized allocation + rationale

### Phase 3 — pybind11 bridge
- Wrap C++ engine, expose `optimize()`/`backtest()` to Python
- Integration test: Python calls into C++, validates output shape/values
- **Deliverable:** FastAPI can call the C++ engine directly

### Phase 4 — API layer
- Implement all four endpoints
- Wire to Postgres
- **Deliverable:** full request/response cycle works via API client (e.g. curl/Postman)

### Phase 5 — Frontend
- Questionnaire UI → dashboard shell
- Allocation pie chart, performance line chart, rebalance alerts
- **Deliverable:** working demo, click-through from questionnaire to dashboard

### Phase 6 — Polish & deploy
- Docker: compile C++ lib + pybind11 module inside build
- Deploy backend (Railway/Render), frontend (Vercel)
- Seed 3-4 realistic demo profiles
- Write README (architecture diagram, key metrics)
- Record 60-second demo video/gif

## 9. Defensibility checklist

Before putting this on a resume, be able to answer:

- **Why C++ here?** Point to a concrete bottleneck (covariance matrix ops, backtest
  over long time series) and have a benchmark number (e.g. "Nx faster than NumPy
  equivalent") ready.
- **The math, cold:** what mean-variance optimization minimizes/maximizes, why
  covariance matrices can be ill-conditioned, what Ledoit-Wolf shrinkage does if used.
- **Real numbers:** actual backtested CAGR/Sharpe/drawdown figures, not placeholders,
  and a reason for any under/over-performance in specific years.
- **Known limitations, stated proactively:** MPT assumes historical returns predict
  future returns, assumes normal distribution (no fat tails), ignores taxes and
  transaction costs.
- **Code fluency:** be able to open and walk through the optimizer and rebalance-check
  functions line by line.
- **"If I had more time" list:** transaction cost modeling, tax-aware rebalancing,
  factor models (Fama-French) instead of pure MPT, walk-forward backtesting.

## 10. Target resume bullet

> Built a robo-advisor applying Modern Portfolio Theory for portfolio optimization
> (C++ core via pybind11, FastAPI, Next.js), backtested against 10 years of market
> data showing [X]% CAGR vs S&P 500's [Y]%, with automated drift-based rebalancing.