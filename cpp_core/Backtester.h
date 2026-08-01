#pragma once
#include <Eigen/Dense>
#include <vector>

struct BacktestResult {
    double cagr;
    double sharpe_ratio;
    double max_drawdown;
    std::vector<double> portfolio_value_over_time;
};

class Backtester {
public:
    // historical_prices: N_Assets x N_Observations
    // weights: 1 x N_Assets
    static BacktestResult run(
        Eigen::MatrixXd historical_prices,
        Eigen::VectorXd weights,
        double risk_free_rate = 0.02
    );
};
