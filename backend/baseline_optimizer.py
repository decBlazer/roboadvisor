import numpy as pd
import numpy as np
from scipy.optimize import minimize
import time

def mean_variance_optimization(expected_returns, cov_matrix, risk_free_rate=0.02):
    """
    Given expected returns and a covariance matrix, solves for the portfolio weights
    that maximize the Sharpe ratio. This serves as our NumPy baseline to benchmark
    against the C++ implementation.
    """
    num_assets = len(expected_returns)
    args = (expected_returns, cov_matrix, risk_free_rate)
    
    # We want to maximize Sharpe, which is the same as minimizing negative Sharpe
    def neg_sharpe_ratio(weights, expected_returns, cov_matrix, risk_free_rate):
        p_ret = np.sum(expected_returns * weights)
        p_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return -(p_ret - risk_free_rate) / p_vol
        
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(num_assets))
    
    # Initial guess (equal allocation)
    init_guess = num_assets * [1. / num_assets,]
    
    start_time = time.perf_counter()
    result = minimize(neg_sharpe_ratio, init_guess, args=args,
                        method='SLSQP', bounds=bounds, constraints=constraints)
    end_time = time.perf_counter()
    
    return {
        'weights': result.x,
        'sharpe_ratio': -result.fun,
        'execution_time_seconds': end_time - start_time,
        'success': result.success
    }

if __name__ == "__main__":
    # Dummy data for testing
    expected_returns = np.array([0.10, 0.05, 0.08, 0.12])
    # Make a dummy symmetric positive-definite covariance matrix
    cov_matrix = np.array([
        [0.04, 0.005, 0.01, 0.02],
        [0.005, 0.02, 0.008, 0.003],
        [0.01, 0.008, 0.05, 0.015],
        [0.02, 0.003, 0.015, 0.06]
    ])
    
    print("Running baseline Python/NumPy optimizer...")
    result = mean_variance_optimization(expected_returns, cov_matrix)
    print(f"Optimal Weights: {result['weights']}")
    print(f"Max Sharpe Ratio: {result['sharpe_ratio']:.4f}")
    print(f"Execution Time: {result['execution_time_seconds']:.6f} seconds")
