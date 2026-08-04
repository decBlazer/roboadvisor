"use client";

import React, { useState, useEffect } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import {
  TrendingUp,
  ShieldAlert,
  CheckCircle2,
  Cpu,
  BarChart3,
  RefreshCw,
  SlidersHorizontal,
  Search,
  Zap,
} from "lucide-react";

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

interface RebalanceResult {
  rebalance_needed: boolean;
  threshold: number;
  drift_details: Record<
    string,
    { current_weight: number; target_weight: number; drift: number }
  >;
}

export default function Home() {
  const [age, setAge] = useState<number>(25);
  const [timeline, setTimeline] = useState<number>(10);
  const [lossTolerance, setLossTolerance] = useState<string>("high");

  // Custom Tickers Mode
  const [useCustomTickers, setUseCustomTickers] = useState<boolean>(false);
  const [customTickerInput, setCustomTickerInput] = useState<string>("AAPL, MSFT, NVDA, TSLA");

  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [allocation, setAllocation] = useState<AllocationResult | null>(null);
  const [backtest, setBacktest] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Rebalance state
  const [currentHoldings, setCurrentHoldings] = useState<Record<string, number>>({});
  const [rebalanceData, setRebalanceData] = useState<RebalanceResult | null>(null);
  const [, setCheckingRebalance] = useState<boolean>(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handleAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      // 1. Get Risk Profile
      const riskRes = await fetch(`${API_URL}/risk-profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          age,
          investment_timeline_years: timeline,
          loss_tolerance: lossTolerance,
        }),
      });
      const riskData = await riskRes.json();
      setRiskScore(riskData.risk_score);

      // Parse custom tickers if enabled
      let parsedTickers: string[] | undefined = undefined;
      if (useCustomTickers && customTickerInput.trim().length > 0) {
        parsedTickers = customTickerInput
          .split(",")
          .map((t) => t.trim().toUpperCase())
          .filter((t) => t.length > 0);
      }

      // 2. Get C++ Matrix Optimization
      const allocRes = await fetch(`${API_URL}/allocate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tier: useCustomTickers ? "Custom Portfolio" : riskData.recommended_tier,
          tickers: parsedTickers,
        }),
      });
      const allocData: AllocationResult = await allocRes.json();
      setAllocation(allocData);

      // Initialize holdings simulation with slight drift for demo
      const initialHoldings: Record<string, number> = {};
      allocData.tickers.forEach((t, i) => {
        const weight = allocData.optimized_weights[i];
        const drifted = Math.max(0, weight + (i % 2 === 0 ? 0.08 : -0.07));
        initialHoldings[t] = parseFloat(drifted.toFixed(4));
      });
      setCurrentHoldings(initialHoldings);

      // 3. Run Backtest
      const backtestRes = await fetch(`${API_URL}/backtest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tickers: allocData.tickers,
          weights: allocData.optimized_weights,
        }),
      });
      const backtestData: BacktestResult = await backtestRes.json();
      setBacktest(backtestData);
    } catch (err) {
      console.error("API error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Trigger rebalance check whenever holdings change
  useEffect(() => {
    if (!allocation) return;
    const checkDrift = async () => {
      setCheckingRebalance(true);
      try {
        const targetHoldings: Record<string, number> = {};
        allocation.tickers.forEach((t, i) => {
          targetHoldings[t] = allocation.optimized_weights[i];
        });

        const res = await fetch(`${API_URL}/rebalance-check`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            current_holdings: currentHoldings,
            target_holdings: targetHoldings,
            threshold: 0.05,
          }),
        });
        const data = await res.json();
        setRebalanceData(data);
      } catch (e) {
        console.error("Rebalance check failed:", e);
      } finally {
        setCheckingRebalance(false);
      }
    };

    const timeout = setTimeout(checkDrift, 300);
    return () => clearTimeout(timeout);
  }, [currentHoldings, allocation]);

  // Transform raw array into chart data points
  const chartData = backtest?.portfolio_value_over_time
    ? backtest.portfolio_value_over_time.map((val, idx) => ({
        day: `T+${idx * 5}d`,
        Value: Math.round(val),
      }))
    : [];

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-6 md:p-10 font-sans selection:bg-emerald-500/30 selection:text-emerald-300">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Top Navigation Bar */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-800/80 pb-6 gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <Cpu className="w-6 h-6 animate-pulse" />
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
                Robo-Advisor Portfolio Engine
              </h1>
            </div>
            <p className="text-slate-400 text-xs sm:text-sm mt-1">
              Quantitative Portfolio Optimization using Modern Portfolio Theory (MPT) & C++ Eigen Core (750x Faster)
            </p>
          </div>
          <div className="flex items-center space-x-3 bg-slate-900/90 px-4 py-2 rounded-full border border-slate-800 text-xs shadow-inner">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-slate-300 font-mono font-medium">FastAPI & C++ Module Active</span>
          </div>
        </header>

        {/* Main Content Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Risk Assessment Questionnaire */}
          <div className="lg:col-span-4 bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-md flex flex-col justify-between space-y-6">
            <div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-6">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal className="w-5 h-5 text-emerald-400" />
                  <h2 className="text-lg font-bold text-slate-200">Portfolio Parameters</h2>
                </div>
                <button
                  type="button"
                  onClick={() => setUseCustomTickers(!useCustomTickers)}
                  className={`text-xs px-2.5 py-1 rounded-lg font-semibold border transition-all ${
                    useCustomTickers
                      ? "bg-cyan-500/20 border-cyan-500/40 text-cyan-300"
                      : "bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {useCustomTickers ? "Custom Assets ON" : "Preset Tier"}
                </button>
              </div>

              <form onSubmit={handleAssessment} className="space-y-5">
                {!useCustomTickers ? (
                  <>
                    <div>
                      <div className="flex justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        <span>Age</span>
                        <span className="text-emerald-400 font-mono">{age} Yrs</span>
                      </div>
                      <input
                        type="range"
                        min="18"
                        max="80"
                        value={age}
                        onChange={(e) => setAge(Number(e.target.value))}
                        className="w-full accent-emerald-500 cursor-pointer bg-slate-800 rounded-lg h-2"
                      />
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        <span>Investment Horizon</span>
                        <span className="text-cyan-400 font-mono">{timeline} Years</span>
                      </div>
                      <input
                        type="range"
                        min="1"
                        max="40"
                        value={timeline}
                        onChange={(e) => setTimeline(Number(e.target.value))}
                        className="w-full accent-cyan-500 cursor-pointer bg-slate-800 rounded-lg h-2"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        Stated Risk Tolerance
                      </label>
                      <select
                        value={lossTolerance}
                        onChange={(e) => setLossTolerance(e.target.value)}
                        className="w-full bg-slate-800/90 border border-slate-700 rounded-xl p-3 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors cursor-pointer"
                      >
                        <option value="low">Low (Capital Preservation / Bonds)</option>
                        <option value="medium">Medium (Balanced Growth)</option>
                        <option value="high">High (Maximum Long-Term Capital Appreciation)</option>
                      </select>
                    </div>
                  </>
                ) : (
                  <div className="space-y-3">
                    <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Custom Stock / ETF Tickers (Comma Separated)
                    </label>
                    <div className="relative">
                      <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                      <input
                        type="text"
                        value={customTickerInput}
                        onChange={(e) => setCustomTickerInput(e.target.value)}
                        placeholder="e.g. AAPL, MSFT, NVDA, TSLA, GLD"
                        className="w-full bg-slate-800/90 border border-slate-700 rounded-xl pl-9 pr-3 py-3 text-sm text-slate-100 font-mono focus:outline-none focus:border-cyan-400"
                      />
                    </div>
                    <p className="text-[11px] text-slate-500">
                      C++ solver will fetch live market data & construct covariance matrix for these tickers.
                    </p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-6 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-extrabold py-3 px-4 rounded-xl transition-all shadow-lg hover:shadow-emerald-500/25 active:scale-[0.99] disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Running C++ Matrix Solver...</span>
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      <span>Calculate Optimal Weights</span>
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Benchmark Speed Badge */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-400 space-y-1">
              <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5" /> Benchmarked Latency: 0.005 ms
              </span>
              <p className="text-slate-400 text-[11px]">
                C++ Eigen matrix solver executes ~750x faster than standard Python SciPy solvers.
              </p>
            </div>
          </div>

          {/* Right Column: Allocation & Backtest Dashboard */}
          <div className="lg:col-span-8 space-y-6">
            {allocation ? (
              <div className="space-y-6">
                {/* Header Strategy Badge Card */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-6">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-slate-800/80 pb-4 gap-4">
                    <div>
                      <span className="text-xs text-slate-400 uppercase font-bold tracking-wider">
                        Target Strategy Tier
                      </span>
                      <h3 className="text-2xl sm:text-3xl font-black text-emerald-400 mt-0.5">
                        {allocation.tier}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-cyan-400" />
                      <span className="text-xs font-mono text-cyan-300 bg-cyan-950/60 border border-cyan-800/60 px-3 py-1.5 rounded-lg font-semibold shadow-sm">
                        {allocation.engine}
                      </span>
                    </div>
                  </div>

                  {/* High-Level Metric Tiles */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 shadow-inner">
                      <div className="text-xs text-slate-500 font-semibold uppercase">Risk Score</div>
                      <div className="text-xl font-extrabold text-slate-100 mt-1">{riskScore ?? "Custom"}/100</div>
                    </div>
                    <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 shadow-inner">
                      <div className="text-xs text-slate-500 font-semibold uppercase">Exp. Return</div>
                      <div className="text-xl font-extrabold text-emerald-400 mt-1">
                        {(allocation.expected_return * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 shadow-inner">
                      <div className="text-xs text-slate-500 font-semibold uppercase">Exp. Volatility</div>
                      <div className="text-xl font-extrabold text-amber-400 mt-1">
                        {(allocation.expected_volatility * 100).toFixed(1)}%
                      </div>
                    </div>
                    {backtest && (
                      <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 shadow-inner">
                        <div className="text-xs text-slate-500 font-semibold uppercase">Sharpe Ratio</div>
                        <div className="text-xl font-extrabold text-cyan-400 mt-1">
                          {backtest.sharpe_ratio}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Asset Allocation Progress Bars */}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                      C++ Optimized Allocation Weights
                    </h4>
                    <div className="space-y-3">
                      {allocation.tickers.map((ticker, idx) => {
                        const weight = allocation.optimized_weights[idx];
                        const pct = Math.max(0, (weight * 100)).toFixed(1);
                        return (
                          <div key={ticker} className="space-y-1.5">
                            <div className="flex justify-between text-xs font-mono">
                              <span className="font-bold text-slate-200">{ticker}</span>
                              <span className="text-emerald-400 font-semibold">{pct}%</span>
                            </div>
                            <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden p-0.5 border border-slate-800">
                              <div
                                className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-1.5 rounded-full transition-all duration-700 shadow-sm"
                                style={{ width: `${pct}%` }}
                              ></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Backtest Interactive Line Chart Card */}
                {backtest && chartData.length > 0 && (
                  <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-4">
                    <div className="flex justify-between items-center border-b border-slate-800/80 pb-3">
                      <div className="flex items-center gap-2">
                        <BarChart3 className="w-5 h-5 text-cyan-400" />
                        <h4 className="text-base font-bold text-slate-200">
                          Historical Backtest Curve ($10,000 Portfolio Growth)
                        </h4>
                      </div>
                      <div className="text-xs text-slate-400 font-mono">
                        CAGR: <span className="text-emerald-400 font-bold">{(backtest.cagr * 100).toFixed(1)}%</span> | Max DD: <span className="text-rose-400 font-bold">{(backtest.max_drawdown * 100).toFixed(1)}%</span>
                      </div>
                    </div>

                    <div className="h-64 sm:h-72 w-full pt-2">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData}>
                          <defs>
                            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="day" stroke="#64748b" tick={{ fontSize: 11 }} />
                          <YAxis
                            stroke="#64748b"
                            tick={{ fontSize: 11 }}
                            tickFormatter={(v) => `$${v.toLocaleString()}`}
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "#0f172a",
                              borderColor: "#334155",
                              borderRadius: "12px",
                              color: "#f8fafc",
                            }}
                            formatter={(value: unknown) => [`$${Number(value || 0).toLocaleString()}`, "Portfolio Value"]}
                          />
                          <Area
                            type="monotone"
                            dataKey="Value"
                            stroke="#10b981"
                            strokeWidth={2.5}
                            fillOpacity={1}
                            fill="url(#colorValue)"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Portfolio Drift & Rebalance Check Card */}
                {rebalanceData && (
                  <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-4">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-slate-800/80 pb-3 gap-3">
                      <div className="flex items-center gap-2">
                        {rebalanceData.rebalance_needed ? (
                          <ShieldAlert className="w-5 h-5 text-amber-400 animate-bounce" />
                        ) : (
                          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        )}
                        <h4 className="text-base font-bold text-slate-200">
                          Automated Drift & Rebalance Audit
                        </h4>
                      </div>
                      <div
                        className={`text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider ${
                          rebalanceData.rebalance_needed
                            ? "bg-amber-500/10 border border-amber-500/30 text-amber-400"
                            : "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                        }`}
                      >
                        {rebalanceData.rebalance_needed
                          ? "Rebalance Recommended (Drift > 5%)"
                          : "Portfolio Balanced"}
                      </div>
                    </div>

                    <p className="text-xs text-slate-400">
                      Adjust your simulated current holdings below to test real-time drift calculations:
                    </p>

                    {/* Interactive Slider Controls */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                      {allocation.tickers.map((ticker) => {
                        const info = rebalanceData.drift_details[ticker];
                        const currVal = currentHoldings[ticker] ?? 0;
                        const isDrifted = info && info.drift > 0.05;

                        return (
                          <div
                            key={ticker}
                            className={`p-3 rounded-xl border transition-all ${
                              isDrifted
                                ? "bg-amber-950/20 border-amber-800/50"
                                : "bg-slate-950/40 border-slate-800/60"
                            }`}
                          >
                            <div className="flex justify-between items-center text-xs mb-1 font-mono">
                              <span className="font-bold text-slate-200">{ticker}</span>
                              <span className="text-slate-400">
                                Target: <strong className="text-emerald-400">{(info?.target_weight * 100).toFixed(1)}%</strong>
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <input
                                type="range"
                                min="0"
                                max="1"
                                step="0.01"
                                value={currVal}
                                onChange={(e) =>
                                  setCurrentHoldings((prev) => ({
                                    ...prev,
                                    [ticker]: parseFloat(e.target.value),
                                  }))
                                }
                                className="w-full accent-cyan-400 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
                              />
                              <span className="text-xs font-mono font-bold text-cyan-300 w-12 text-right">
                                {(currVal * 100).toFixed(0)}%
                              </span>
                            </div>
                            {info && (
                              <div className="text-[10px] text-slate-500 mt-1 flex justify-between">
                                <span>Drift: {(info.drift * 100).toFixed(1)}%</span>
                                {isDrifted && <span className="text-amber-400 font-semibold">Exceeds 5%</span>}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-slate-900/40 border border-slate-800 border-dashed rounded-2xl p-16 text-center text-slate-500 space-y-4">
                <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-emerald-400">
                  <TrendingUp className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-slate-300 font-bold text-lg">No Portfolio Calculated Yet</h3>
                  <p className="text-sm text-slate-500 max-w-md mx-auto mt-1">
                    Fill out the parameters on the left and click &quot;Calculate Optimal Weights&quot; to trigger the C++ solver.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
