#include "Backtester.h"
#include <cmath>
#include <algorithm>

BacktestResult Backtester::run(
    Eigen::MatrixXd historical_prices,
    Eigen::VectorXd weights,
    double risk_free_rate)
{
    BacktestResult result;
    int n_assets = historical_prices.rows();
    int n_obs = historical_prices.cols();
    
    if (n_assets == 0 || n_obs == 0) return result;

    // Calculate daily portfolio returns
    // First, convert prices to percentage returns
    Eigen::MatrixXd daily_returns(n_assets, n_obs - 1);
    for (int i = 0; i < n_assets; ++i) {
        for (int j = 1; j < n_obs; ++j) {
            daily_returns(i, j - 1) = (historical_prices(i, j) - historical_prices(i, j - 1)) / historical_prices(i, j - 1);
        }
    }

    // Portfolio daily return is matrix product of transpose(returns) and weights (N_obs-1 x 1)
    Eigen::VectorXd port_daily_returns = daily_returns.transpose() * weights;

    // Simulate portfolio value over time
    double initial_value = 10000.0;
    result.portfolio_value_over_time.push_back(initial_value);
    
    double current_value = initial_value;
    double peak_value = initial_value;
    double max_dd = 0.0;
    
    for (int j = 0; j < port_daily_returns.size(); ++j) {
        current_value *= (1.0 + port_daily_returns(j));
        result.portfolio_value_over_time.push_back(current_value);
        
        if (current_value > peak_value) {
            peak_value = current_value;
        }
        
        double drawdown = (peak_value - current_value) / peak_value;
        if (drawdown > max_dd) {
            max_dd = drawdown;
        }
    }

    result.max_drawdown = max_dd;

    // Calculate CAGR (assuming 252 trading days per year)
    double total_return = current_value / initial_value;
    double years = static_cast<double>(n_obs) / 252.0;
    result.cagr = std::pow(total_return, 1.0 / years) - 1.0;

    // Calculate annualized Sharpe ratio
    double mean_daily_return = port_daily_returns.mean();
    Eigen::VectorXd centered = port_daily_returns.array() - mean_daily_return;
    double variance = centered.squaredNorm() / (port_daily_returns.size() - 1.0);
    double std_dev = std::sqrt(variance);
    
    // Annualize (multiply by sqrt(252))
    double ann_return = mean_daily_return * 252.0;
    double ann_vol = std_dev * std::sqrt(252.0);
    
    result.sharpe_ratio = (ann_return - risk_free_rate) / ann_vol;

    return result;
}
