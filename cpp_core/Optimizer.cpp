#include "Optimizer.h"
#include <iostream>

Eigen::VectorXd Optimizer::maximize_sharpe_ratio(
    const std::vector<Asset>& assets, 
    const Eigen::MatrixXd& cov_matrix, 
    double risk_free_rate) 
{
    int num_assets = assets.size();
    Eigen::VectorXd excess_returns(num_assets);
    
    for (int i = 0; i < num_assets; ++i) {
        excess_returns(i) = assets[i].expected_return - risk_free_rate;
    }

    // Unconstrained tangency portfolio formula: W = Cov^-1 * ExcessReturns
    // In Eigen, we use the .inverse() method or solve a linear system.
    // Solving a linear system is numerically more stable than direct inversion.
    // cov_matrix * W = excess_returns
    Eigen::VectorXd unnormalized_weights = cov_matrix.colPivHouseholderQr().solve(excess_returns);

    // Normalize weights so they sum to 1.0 (100% of the portfolio)
    double sum_weights = unnormalized_weights.sum();
    Eigen::VectorXd final_weights = unnormalized_weights / sum_weights;

    return final_weights;
}

Eigen::MatrixXd Optimizer::calculate_covariance_matrix(const Eigen::MatrixXd& historical_returns) 
{
    // historical_returns should be (N_Assets x N_Observations)
    // Demean the returns
    Eigen::VectorXd mean_returns = historical_returns.rowwise().mean();
    Eigen::MatrixXd centered_returns = historical_returns.colwise() - mean_returns;

    // Calculate covariance: (Centered * Centered^T) / (N_Observations - 1)
    double n_obs = historical_returns.cols();
    Eigen::MatrixXd cov = (centered_returns * centered_returns.transpose()) / (n_obs - 1.0);
    
    return cov;
}
