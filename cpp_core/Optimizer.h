#pragma once
#include <Eigen/Dense>
#include <vector>
#include "Portfolio.h"

class Optimizer {
public:
    // Calculates the Tangency Portfolio (Maximum Sharpe Ratio) weights
    // using the closed-form solution: W = Cov_Inverse * (ExpectedReturns - RiskFreeRate)
    static Eigen::VectorXd maximize_sharpe_ratio(
        const std::vector<Asset>& assets, 
        const Eigen::MatrixXd& cov_matrix, 
        double risk_free_rate = 0.02
    );

    // Creates the covariance matrix from historical returns
    static Eigen::MatrixXd calculate_covariance_matrix(
        const Eigen::MatrixXd& historical_returns
    );
};
