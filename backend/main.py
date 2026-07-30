from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from ingest_data import get_historical_data
from baseline_optimizer import mean_variance_optimization

# Try importing compiled C++ module if available; fallback to Python baseline
try:
    import roboadvisor_core
    CPP_CORE_AVAILABLE = True
except ImportError:
    CPP_CORE_AVAILABLE = False

app = FastAPI(title="Robo-Advisor API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Preset Allocation Tiers (Stock / Bond ratio baseline)
TIER_PRESETS = {
    "Conservative": {"tickers": ["SPY", "TLT", "IEF", "GLD"], "target_weights": [0.20, 0.40, 0.30, 0.10]},
    "Moderate-Conservative": {"tickers": ["SPY", "TLT", "IEF", "GLD"], "target_weights": [0.40, 0.30, 0.20, 0.10]},
    "Moderate": {"tickers": ["SPY", "QQQ", "TLT", "GLD"], "target_weights": [0.50, 0.20, 0.20, 0.10]},
    "Growth": {"tickers": ["SPY", "QQQ", "TLT", "GLD"], "target_weights": [0.60, 0.25, 0.10, 0.05]},
    "Aggressive": {"tickers": ["SPY", "QQQ", "GLD", "IWM"], "target_weights": [0.60, 0.30, 0.05, 0.05]},
}

class RiskProfileRequest(BaseModel):
    age: int
    investment_timeline_years: int
    loss_tolerance: str  # "low", "medium", "high"

class AllocationRequest(BaseModel):
    tier: str
    tickers: Optional[List[str]] = None

class BacktestRequest(BaseModel):
    tickers: List[str]
    weights: List[float]
    start_date: Optional[str] = "2018-01-01"
    end_date: Optional[str] = "2024-01-01"

class RebalanceCheckRequest(BaseModel):
    current_holdings: Dict[str, float]  # ticker -> current_weight
    target_holdings: Dict[str, float]   # ticker -> target_weight
    threshold: Optional[float] = 0.05

@app.get("/")
def read_root():
    return {
        "status": "ok", 
        "message": "Robo-Advisor API is running",
        "cpp_engine_active": CPP_CORE_AVAILABLE
    }

@app.post("/risk-profile")
def get_risk_profile(request: RiskProfileRequest):
    score = 50  # Base score
    
    # Age factor
    if request.age < 30:
        score += 20
    elif request.age < 50:
        score += 10
    else:
        score -= 10
        
    # Timeline factor
    if request.investment_timeline_years > 10:
        score += 20
    elif request.investment_timeline_years > 5:
        score += 10
    
    # Loss tolerance factor
    if request.loss_tolerance.lower() == "high":
        score += 25
    elif request.loss_tolerance.lower() == "medium":
        score += 10
    elif request.loss_tolerance.lower() == "low":
        score -= 15
        
    score = max(0, min(100, score))
    
    if score < 25:
        tier = "Conservative"
    elif score < 45:
        tier = "Moderate-Conservative"
    elif score < 65:
        tier = "Moderate"
    elif score < 85:
        tier = "Growth"
    else:
        tier = "Aggressive"
        
    return {
        "risk_score": score,
        "recommended_tier": tier,
        "preset_allocation": TIER_PRESETS.get(tier)
    }

@app.post("/allocate")
def allocate_portfolio(request: AllocationRequest):
    tier_info = TIER_PRESETS.get(request.tier)
    if not tier_info:
        raise HTTPException(status_code=400, detail="Invalid risk tier")
        
    tickers = request.tickers if request.tickers else tier_info["tickers"]
    
    # Fetch historical data
    df = get_historical_data(tickers, "2018-01-01", "2024-01-01")
    if df.empty:
        raise HTTPException(status_code=500, detail="Failed to fetch market data")
        
    returns = df.pct_change().dropna()
    exp_returns = returns.mean().values * 252  # Annualized expected return
    cov_matrix = returns.cov().values * 252   # Annualized covariance
    
    if CPP_CORE_AVAILABLE:
        # Use C++ pybind11 module
        assets = [roboadvisor_core.Asset(t, exp_returns[i], np.sqrt(cov_matrix[i, i])) for i, t in enumerate(tickers)]
        opt_weights = roboadvisor_core.maximize_sharpe_ratio(assets, cov_matrix, 0.02)
        engine_used = "C++ Eigen Engine"
    else:
        # Fallback to Python/NumPy baseline
        res = mean_variance_optimization(exp_returns, cov_matrix)
        opt_weights = res["weights"].tolist()
        engine_used = "Python NumPy Baseline"
        
    return {
        "tier": request.tier,
        "engine": engine_used,
        "tickers": tickers,
        "optimized_weights": [round(w, 4) for w in opt_weights],
        "expected_return": float(np.sum(np.array(opt_weights) * exp_returns)),
        "expected_volatility": float(np.sqrt(np.dot(np.array(opt_weights).T, np.dot(cov_matrix, opt_weights))))
    }

@app.post("/backtest")
def backtest_portfolio(request: BacktestRequest):
    df = get_historical_data(request.tickers, request.start_date, request.end_date)
    if df.empty:
        raise HTTPException(status_code=500, detail="Failed to fetch historical data")
        
    weights = np.array(request.weights)
    if abs(sum(weights) - 1.0) > 0.01:
        weights = weights / sum(weights)
        
    if CPP_CORE_AVAILABLE:
        res = roboadvisor_core.run_backtest(df.values.T, weights, 0.02)
        return {
            "engine": "C++ Engine",
            "cagr": round(res.cagr, 4),
            "sharpe_ratio": round(res.sharpe_ratio, 4),
            "max_drawdown": round(res.max_drawdown, 4),
            "portfolio_value_over_time": res.portfolio_value_over_time[::5] # downsample for chart
        }
    else:
        # Python implementation of backtest
        returns = df.pct_change().dropna()
        port_daily = (returns * weights).sum(axis=1)
        cum_returns = (1 + port_daily).cumprod()
        initial_val = 10000.0
        val_over_time = (cum_returns * initial_val).tolist()
        
        total_return = val_over_time[-1] / initial_val
        years = len(port_daily) / 252.0
        cagr = (total_return ** (1.0 / years)) - 1.0
        
        peak = np.maximum.accumulate(val_over_time)
        drawdowns = (peak - val_over_time) / peak
        max_dd = float(np.max(drawdowns))
        
        ann_return = port_daily.mean() * 252
        ann_vol = port_daily.std() * np.sqrt(252)
        sharpe = (ann_return - 0.02) / ann_vol
        
        return {
            "engine": "Python Fallback",
            "cagr": round(cagr, 4),
            "sharpe_ratio": round(sharpe, 4),
            "max_drawdown": round(max_dd, 4),
            "portfolio_value_over_time": val_over_time[::5]  # downsample for UI charting
        }

@app.post("/rebalance-check")
def rebalance_check(request: RebalanceCheckRequest):
    rebalance_needed = False
    drift_details = {}
    
    for ticker, target_w in request.target_holdings.items():
        curr_w = request.current_holdings.get(ticker, 0.0)
        drift = abs(curr_w - target_w)
        drift_details[ticker] = {
            "current_weight": curr_w,
            "target_weight": target_w,
            "drift": round(drift, 4)
        }
        if drift > request.threshold:
            rebalance_needed = True
            
    return {
        "rebalance_needed": rebalance_needed,
        "threshold": request.threshold,
        "drift_details": drift_details
    }
