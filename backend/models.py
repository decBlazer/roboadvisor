from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
try:
    from database import Base
except ImportError:
    from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    risk_profile = relationship("RiskProfile", back_populates="user", uselist=False)
    portfolios = relationship("Portfolio", back_populates="user")

class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    age = Column(Integer, nullable=False)
    timeline_years = Column(Integer, nullable=False)
    loss_tolerance = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)
    recommended_tier = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="risk_profile")

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tier = Column(String, nullable=False)
    engine_used = Column(String, nullable=False)
    target_allocation_json = Column(JSON, nullable=False)
    expected_return = Column(Float, nullable=False)
    expected_volatility = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="portfolios")
    rebalance_events = relationship("RebalanceEvent", back_populates="portfolio")

class RebalanceEvent(Base):
    __tablename__ = "rebalance_events"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    rebalance_needed = Column(Boolean, nullable=False)
    drift_details_json = Column(JSON, nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="rebalance_events")
