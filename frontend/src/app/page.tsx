"use client";

import React, { useState } from "react";

interface AllocationResult {
  tier: string;
  engine: string;
  tickers: string[];
  optimized_weights: number[];
  expected_return: number;
  expected_volatility: number;
}

interface BacktestResult {
  engine: string;
  cagr: number;
  sharpe_ratio: number;
  max_drawdown: number;
  portfolio_value_over_time: number[];
}

export default function Home() {
  const [age, setAge] = useState<number>(25);
  const [timeline, setTimeline] = useState<number>(10);
  const [lossTolerance, setLossTolerance] = useState<string>("high");
  
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [recommendedTier, setRecommendedTier] = useState<string>("");
  const [allocation, setAllocation] = useState<AllocationResult | null>(null);
  const [backtest, setBacktest] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const API_URL = "http://localhost:8000";

  const handleAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      // 1. Get Risk Profile
      const riskRes = await fetch(`${API_URL}/risk-profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ age, investment_timeline_years: timeline, loss_tolerance: lossTolerance }),
      });
      const riskData = await riskRes.json();
      setRiskScore(riskData.risk_score);
      setRecommendedTier(riskData.recommended_tier);

      // 2. Get Optimization
      const allocRes = await fetch(`${API_URL}/allocate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tier: riskData.recommended_tier }),
      });
      const allocData = await allocRes.json();
      setAllocation(allocData);

      // 3. Run Backtest
      const backtestRes = await fetch(`${API_URL}/backtest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tickers: allocData.tickers,
          weights: allocData.optimized_weights,
        }),
      });
      const backtestData = await backtestRes.json();
      setBacktest(backtestData);
    } catch (err) {
      console.error("API error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-800 pb-6 gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl font-extrabold bg-gradient-to-r from-emerald-400 to-cyan-500 bg-clip-text text-transparent">
              Robo-Advisor Portfolio Engine
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Quantitative Portfolio Optimization using Modern Portfolio Theory (MPT) & C++ Eigen
            </p>
          </div>
          <div className="flex items-center space-x-2 bg-slate-900 px-3 py-1.5 rounded-full border border-slate-800 text-xs">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-slate-300 font-medium">FastAPI & C++ Ready</span>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Card 1: Questionnaire */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm">
            <h2 className="text-xl font-bold text-slate-200 mb-4 flex items-center gap-2">
              <span>📋</span> Risk Assessment
            </h2>
            <form onSubmit={handleAssessment} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Age ({age})
                </label>
                <input
                  type="range"
                  min="18"
                  max="80"
                  value={age}
                  onChange={(e) => setAge(Number(e.target.value))}
                  className="w-full accent-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Investment Horizon ({timeline} Years)
                </label>
                <input
                  type="range"
                  min="1"
                  max="40"
                  value={timeline}
                  onChange={(e) => setTimeline(Number(e.target.value))}
                  className="w-full accent-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Loss Tolerance
                </label>
                <select
                  value={lossTolerance}
                  onChange={(e) => setLossTolerance(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  <option value="low">Low (Capital Preservation)</option>
                  <option value="medium">Medium (Balanced)</option>
                  <option value="high">High (Maximum Growth)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-4 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-slate-950 font-bold py-2.5 px-4 rounded-lg transition-all shadow-lg hover:shadow-emerald-500/20 disabled:opacity-50"
              >
                {loading ? "Optimizing Portfolio..." : "Calculate Optimal Portfolio"}
              </button>
            </form>
          </div>

          {/* Card 2: Optimization Results */}
          <div className="lg:col-span-2 space-y-6">
            {allocation ? (
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
                <div className="flex justify-between items-center border-b border-slate-800 pb-4">
                  <div>
                    <span className="text-xs text-slate-400 uppercase font-semibold">Recommended Strategy</span>
                    <h3 className="text-2xl font-black text-emerald-400">{allocation.tier}</h3>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 uppercase font-semibold">Engine Executed</span>
                    <div className="text-sm font-mono text-cyan-400 bg-cyan-950/50 border border-cyan-800/50 px-2.5 py-1 rounded">
                      {allocation.engine}
                    </div>
                  </div>
                </div>

                {/* Metrics row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800">
                    <div className="text-xs text-slate-500 font-semibold">Risk Score</div>
                    <div className="text-lg font-bold text-slate-200">{riskScore}/100</div>
                  </div>
                  <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800">
                    <div className="text-xs text-slate-500 font-semibold">Exp. Return</div>
                    <div className="text-lg font-bold text-emerald-400">{(allocation.expected_return * 100).toFixed(1)}%</div>
                  </div>
                  <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800">
                    <div className="text-xs text-slate-500 font-semibold">Exp. Volatility</div>
                    <div className="text-lg font-bold text-amber-400">{(allocation.expected_volatility * 100).toFixed(1)}%</div>
                  </div>
                  {backtest && (
                    <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800">
                      <div className="text-xs text-slate-500 font-semibold">Sharpe Ratio</div>
                      <div className="text-lg font-bold text-cyan-400">{backtest.sharpe_ratio}</div>
                    </div>
                  )}
                </div>

                {/* Holdings Weights */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Optimal Asset Allocation Weights</h4>
                  <div className="space-y-2">
                    {allocation.tickers.map((ticker, idx) => {
                      const weight = allocation.optimized_weights[idx];
                      const pct = (weight * 100).toFixed(1);
                      return (
                        <div key={ticker} className="space-y-1">
                          <div className="flex justify-between text-xs font-mono">
                            <span className="font-bold text-slate-300">{ticker}</span>
                            <span className="text-emerald-400">{pct}%</span>
                          </div>
                          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div
                              className="bg-gradient-to-r from-emerald-500 to-cyan-500 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${pct}%` }}
                            ></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Backtest Statistics */}
                {backtest && (
                  <div className="border-t border-slate-800 pt-4 grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-xs text-slate-500">Historical CAGR</div>
                      <div className="text-base font-bold text-emerald-400">{(backtest.cagr * 100).toFixed(2)}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">Max Drawdown</div>
                      <div className="text-base font-bold text-rose-400">{(backtest.max_drawdown * 100).toFixed(2)}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">Simulated Growth</div>
                      <div className="text-base font-bold text-slate-200">
                        ${backtest.portfolio_value_over_time[backtest.portfolio_value_over_time.length - 1]?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-slate-900/40 border border-slate-800 border-dashed rounded-xl p-12 text-center text-slate-500">
                <p className="text-base">Fill out the Risk Assessment on the left to calculate your optimal MPT portfolio allocation.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
