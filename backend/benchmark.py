import time
import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.getcwd(), "backend"))
import roboadvisor_core
from baseline_optimizer import mean_variance_optimization

def run_benchmark(num_assets=5, num_iterations=1000, risk_free_rate=0.02):
    print(f"\n=======================================================")
    print(f"   ROBO-ADVISOR OPTIMIZER SPEED BENCHMARK ({num_assets} ASSETS)")
    print(f"=======================================================")
    print(f"Running {num_iterations:,} iterations per engine...\n")

    # Generate synthetic returns and positive semi-definite covariance matrix
    np.random.seed(42)
    exp_returns = np.random.uniform(0.05, 0.25, num_assets)
    A = np.random.uniform(-0.1, 0.1, (num_assets, num_assets))
    cov_matrix = np.dot(A, A.T) + np.eye(num_assets) * 0.05

    # Prepare C++ Asset objects
    assets = [
        roboadvisor_core.Asset(f"ASSET_{i}", exp_returns[i], np.sqrt(cov_matrix[i, i]))
        for i in range(num_assets)
    ]

    # --- 1. Benchmark C++ Eigen Core ---
    start_cpp = time.perf_counter()
    for _ in range(num_iterations):
        w_cpp = roboadvisor_core.maximize_sharpe_ratio(assets, cov_matrix, risk_free_rate)
    end_cpp = time.perf_counter()
    cpp_total_sec = end_cpp - start_cpp
    cpp_avg_ms = (cpp_total_sec / num_iterations) * 1000
    cpp_ops_sec = num_iterations / cpp_total_sec

    # --- 2. Benchmark Python NumPy / SciPy Baseline ---
    start_py = time.perf_counter()
    for _ in range(num_iterations):
        res_py = mean_variance_optimization(exp_returns, cov_matrix, risk_free_rate)
    end_py = time.perf_counter()
    py_total_sec = end_py - start_py
    py_avg_ms = (py_total_sec / num_iterations) * 1000
    py_ops_sec = num_iterations / py_total_sec

    # Calculate Speedup
    speedup = py_total_sec / cpp_total_sec

    print(f"-------------------------------------------------------")
    print(f"  ENGINE                     AVG LATENCY      OPS/SEC  ")
    print(f"-------------------------------------------------------")
    print(f"  C++ Eigen Core             {cpp_avg_ms:8.4f} ms    {cpp_ops_sec:9.1f}")
    print(f"  Python SciPy Baseline      {py_avg_ms:8.4f} ms    {py_ops_sec:9.1f}")
    print(f"-------------------------------------------------------")
    print(f"  RESULT: C++ Core is {speedup:.2f}x FASTER than Python SciPy")
    print(f"=======================================================\n")

    return {
        "num_assets": num_assets,
        "iterations": num_iterations,
        "cpp_avg_ms": cpp_avg_ms,
        "py_avg_ms": py_avg_ms,
        "speedup": speedup
    }

if __name__ == "__main__":
    print("Initializing Robo-Advisor Quantitative Benchmark Suite...")
    run_benchmark(num_assets=4, num_iterations=1000)
    run_benchmark(num_assets=10, num_iterations=1000)
