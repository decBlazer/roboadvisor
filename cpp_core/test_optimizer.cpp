#include <iostream>
#include <vector>
#include <cmath>
#include <cassert>
#include "Portfolio.h"
#include "Optimizer.h"
#include "Backtester.h"

void test_optimizer_basic() {
    std::cout << "[TEST] Running Optimizer Basic Test..." << std::endl;
    
    std::vector<Asset> assets = {
        Asset("AAPL", 0.15, 0.20),
        Asset("GOOGL", 0.12, 0.18),
        Asset("BND", 0.04, 0.05)
    };

    Eigen::MatrixXd cov(3, 3);
    cov << 0.04, 0.02, 0.001,
           0.02, 0.0324, 0.001,
           0.001, 0.001, 0.0025;

    Eigen::VectorXd weights = Optimizer::maximize_sharpe_ratio(assets, cov, 0.02);
    
    assert(weights.size() == 3);
    double sum = weights.sum();
    assert(std::abs(sum - 1.0) < 1e-5);
    std::cout << "  ✓ Weights sum to 1.0 (Sum: " << sum << ")" << std::endl;
}

void test_covariance_calculation() {
    std::cout << "[TEST] Running Covariance Calculation Test..." << std::endl;

    Eigen::MatrixXd returns(2, 4);
    returns << 0.01, 0.02, -0.01, 0.03,
               0.005, 0.015, -0.005, 0.02;

    Eigen::MatrixXd cov = Optimizer::calculate_covariance_matrix(returns);
    assert(cov.rows() == 2 && cov.cols() == 2);
    assert(cov(0, 0) > 0.0);
    assert(cov(1, 1) > 0.0);
    std::cout << "  ✓ Covariance matrix calculated successfully (2x2)" << std::endl;
}

void test_backtester() {
    std::cout << "[TEST] Running Backtester Test..." << std::endl;

    // 2 assets, 5 observation days
    Eigen::MatrixXd prices(2, 5);
    prices << 100.0, 102.0, 104.0, 103.0, 106.0,
              50.0,  50.5,  51.0,  50.8,  51.5;

    Eigen::VectorXd weights(2);
    weights << 0.6, 0.4;

    BacktestResult res = Backtester::run(prices, weights, 0.02);
    
    assert(res.portfolio_value_over_time.size() == 5);
    assert(res.max_drawdown >= 0.0);
    assert(!std::isnan(res.cagr));
    assert(!std::isnan(res.sharpe_ratio));
    std::cout << "  ✓ Backtester calculated CAGR=" << res.cagr 
              << ", Sharpe=" << res.sharpe_ratio 
              << ", MaxDD=" << res.max_drawdown << std::endl;
}

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "      ROBO-ADVISOR C++ TEST SUITE         " << std::endl;
    std::cout << "==========================================" << std::endl;
    
    test_optimizer_basic();
    test_covariance_calculation();
    test_backtester();

    std::cout << "\nALL C++ TESTS PASSED SUCCESSFULLY! ✓" << std::endl;
    return 0;
}
