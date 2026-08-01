from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

try:
    from backend.ingest_data import get_historical_data
    from backend.baseline_optimizer import mean_variance_optimization
    from backend.database import engine, Base, get_db
    from backend.models import User, RiskProfile, Portfolio, RebalanceEvent
except ImportError:
    from ingest_data import get_historical_data
    from baseline_optimizer import mean_variance_optimization
    from database import engine, Base, get_db
    from models import User, RiskProfile, Portfolio, RebalanceEvent

# Initialize DB tables on startup
Base.metadata.create_all(bind=engine)

# Try importing compiled C++ module if available; fallback to Python baseline
try:
    import roboadvisor_core
    CPP_CORE_AVAILABLE = True
except ImportError:
    CPP_CORE_AVAILABLE = False

app = FastAPI(title="Robo-Advisor API")

# Prometheus Metrics Definitions
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests handled by API",
    ["method", "endpoint", "status_code"]
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Histogram of HTTP request latencies in seconds",
    ["method", "endpoint"]
)
CPP_OPTIMIZER_DURATION_SECONDS = Histogram(
    "cpp_optimizer_duration_seconds",
    "Execution duration of C++ Eigen Sharpe ratio optimizer in seconds"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_telemetry_and_metrics(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time
    
    response.headers["X-Process-Time"] = f"{duration * 1000:.2f}ms"
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "99"
    
    endpoint = request.url.path
    HTTP_REQUESTS_TOTAL.labels(method=request.method, endpoint=endpoint, status_code=response.status_code).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, endpoint=endpoint).observe(duration)
    
    return response

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
    email: Optional[str] = "demo@roboadvisor.com"

class AllocationRequest(BaseModel):
    tier: str
    tickers: Optional[List[str]] = None
    email: Optional[str] = "demo@roboadvisor.com"

class BacktestRequest(BaseModel):
    tickers: List[str]
    weights: List[float]
    start_date: Optional[str] = "2018-01-01"
    end_date: Optional[str] = "2024-01-01"

class RebalanceCheckRequest(BaseModel):
    current_holdings: Dict[str, float]  # ticker -> current_weight
    target_holdings: Dict[str, float]   # ticker -> target_weight
    threshold: Optional[float] = 0.05
    email: Optional[str] = "demo@roboadvisor.com"

def get_or_create_user(db: Session, email: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@app.get("/")
def read_root():
    return {
        "status": "ok", 
        "message": "Robo-Advisor API is running",
        "cpp_engine_active": CPP_CORE_AVAILABLE,
        "database_connected": True
    }

@app.get("/metrics", response_class=PlainTextResponse)
def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health/live")
def liveness_probe():
    return {"status": "alive", "timestamp": time.time()}

@app.get("/health/ready")
def readiness_probe(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected", "cpp_engine": CPP_CORE_AVAILABLE}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unreachable: {e}")

@app.post("/risk-profile")
def get_risk_profile(request: RiskProfileRequest, db: Session = Depends(get_db)):
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

    # Persist in Database
    if request.email:
        user = get_or_create_user(db, request.email)
        # Update or create risk profile
        profile = db.query(RiskProfile).filter(RiskProfile.user_id == user.id).first()
        if not profile:
            profile = RiskProfile(
                user_id=user.id,
                age=request.age,
                timeline_years=request.investment_timeline_years,
                loss_tolerance=request.loss_tolerance,
                risk_score=score,
                recommended_tier=tier
            )
            db.add(profile)
        else:
            profile.age = request.age
            profile.timeline_years = request.investment_timeline_years
            profile.loss_tolerance = request.loss_tolerance
            profile.risk_score = score
            profile.recommended_tier = tier

        db.commit()
        
    return {
        "risk_score": score,
        "recommended_tier": tier,
        "preset_allocation": TIER_PRESETS.get(tier)
    }

@app.post("/allocate")
def allocate_portfolio(request: AllocationRequest, db: Session = Depends(get_db)):
    tier_info = TIER_PRESETS.get(request.tier)
    if not tier_info:
        raise HTTPException(status_code=400, detail="Invalid risk tier")
        
    tickers = request.tickers if request.tickers else tier_info["tickers"]
    
    # Fetch historical data
    df = get_historical_data(tickers, "2018-01-01", "2024-01-01")
    if df.empty:
        raise HTTPException(status_code=500, detail="Failed to fetch market data")
        
    df = df[tickers]
    returns = df.pct_change().dropna()
    exp_returns = returns.mean().values * 252  # Annualized expected return
    cov_matrix = returns.cov().values * 252   # Annualized covariance
    
    if CPP_CORE_AVAILABLE:
        # Use C++ pybind11 module with safe C-contiguous float64 arrays & measure solve time
        cov_matrix_c = np.ascontiguousarray(cov_matrix, dtype=np.float64)
        assets = [roboadvisor_core.Asset(t, float(exp_returns[i]), float(np.sqrt(cov_matrix[i, i]))) for i, t in enumerate(tickers)]
        with CPP_OPTIMIZER_DURATION_SECONDS.time():
            opt_weights = roboadvisor_core.maximize_sharpe_ratio(assets, cov_matrix_c, 0.02)
        engine_used = "C++ Eigen Engine"
    else:
        # Fallback to Python/NumPy baseline
        res = mean_variance_optimization(exp_returns, cov_matrix)
        opt_weights = res["weights"].tolist()
        engine_used = "Python NumPy Baseline"
        
    formatted_weights = [round(w, 4) for w in opt_weights]
    exp_ret = float(np.sum(np.array(opt_weights) * exp_returns))
    exp_vol = float(np.sqrt(np.dot(np.array(opt_weights).T, np.dot(cov_matrix, opt_weights))))

    # Persist Portfolio Record in Database
    if request.email:
        user = get_or_create_user(db, request.email)
        allocation_json = {t: formatted_weights[i] for i, t in enumerate(tickers)}
        portfolio_rec = Portfolio(
            user_id=user.id,
            tier=request.tier,
            engine_used=engine_used,
            target_allocation_json=allocation_json,
            expected_return=exp_ret,
            expected_volatility=exp_vol
        )
        db.add(portfolio_rec)
        db.commit()

    return {
        "tier": request.tier,
        "engine": engine_used,
        "tickers": tickers,
        "optimized_weights": formatted_weights,
        "expected_return": exp_ret,
        "expected_volatility": exp_vol
    }

@app.post("/backtest")
def backtest_portfolio(request: BacktestRequest):
    df = get_historical_data(request.tickers, request.start_date, request.end_date)
    if df.empty:
        raise HTTPException(status_code=500, detail="Failed to fetch historical data")
        
    df = df[request.tickers]
    weights = np.array(request.weights)
    if abs(sum(weights) - 1.0) > 0.01:
        weights = weights / sum(weights)
        
    if CPP_CORE_AVAILABLE:
        prices_c = np.ascontiguousarray(df.values.T, dtype=np.float64)
        weights_c = np.ascontiguousarray(weights, dtype=np.float64)
        res = roboadvisor_core.run_backtest(prices_c, weights_c, 0.02)
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
def rebalance_check(request: RebalanceCheckRequest, db: Session = Depends(get_db)):
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

    # Persist Rebalance Event Log in Database
    if request.email:
        user = get_or_create_user(db, request.email)
        latest_portfolio = (
            db.query(Portfolio)
            .filter(Portfolio.user_id == user.id)
            .order_by(Portfolio.created_at.desc())
            .first()
        )
        if latest_portfolio:
            rebalance_rec = RebalanceEvent(
                portfolio_id=latest_portfolio.id,
                rebalance_needed=rebalance_needed,
                drift_details_json=drift_details
            )
            db.add(rebalance_rec)
            db.commit()
            
    return {
        "rebalance_needed": rebalance_needed,
        "threshold": request.threshold,
        "drift_details": drift_details
    }

@app.get("/user/{email}/history")
def get_user_history(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    profile = db.query(RiskProfile).filter(RiskProfile.user_id == user.id).first()
    portfolios = (
        db.query(Portfolio)
        .filter(Portfolio.user_id == user.id)
        .order_by(Portfolio.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "email": user.email,
        "risk_profile": {
            "age": profile.age,
            "timeline": profile.timeline_years,
            "risk_score": profile.risk_score,
            "tier": profile.recommended_tier
        } if profile else None,
        "saved_portfolios_count": len(portfolios),
        "latest_portfolios": [
            {
                "id": p.id,
                "tier": p.tier,
                "engine": p.engine_used,
                "target_allocation": p.target_allocation_json,
                "created_at": p.created_at.isoformat()
            }
            for p in portfolios
        ]
    }
