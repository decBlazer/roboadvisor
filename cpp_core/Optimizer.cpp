#include "Optimizer.h"
#include <iostream>

Eigen::VectorXd Optimizer::maximize_sharpe_ratio(
    const std::vector<Asset>& assets, 
    Eigen::MatrixXd cov_matrix, 
    double risk_free_rate) 
{
    int num_assets = assets.size();
    Eigen::VectorXd excess_returns(num_assets);
    
    for (int i = 0; i < num_assets; ++i) {
        excess_returns(i) = assets[i].expected_return - risk_free_rate;
    }

    // Add diagonal regularization (shrinkage) to ensure positive-definiteness & numerical stability
    // Cov_reg = Cov + epsilon * I
    const double epsilon = 1e-6;
    Eigen::MatrixXd reg_cov_matrix = cov_matrix + epsilon * Eigen::MatrixXd::Identity(num_assets, num_assets);

    // Solve regularized linear system: Cov_reg * W = excess_returns
    Eigen::VectorXd unnormalized_weights = reg_cov_matrix.colPivHouseholderQr().solve(excess_returns);

    // Normalize weights so they sum to 1.0 (100% of the portfolio)
    double sum_weights = unnormalized_weights.sum();
    if (std::abs(sum_weights) < 1e-9) {
        // Fallback: equal weight allocation if unnormalized sum is near zero
        return Eigen::VectorXd::Constant(num_assets, 1.0 / num_assets);
    }

    Eigen::VectorXd final_weights = unnormalized_weights / sum_weights;
    return final_weights;
}

Eigen::MatrixXd Optimizer::calculate_covariance_matrix(Eigen::MatrixXd historical_returns) 
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
