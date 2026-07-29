#include "Portfolio.h"

// The : m_assets(assets), m_weights(weights) is an initialization list. 
// It's the standard way to initialize fields in C++ (better than doing it inside the {} body).
Portfolio::Portfolio(const std::vector<Asset>& assets, const Eigen::VectorXd& weights) 
    : m_assets(assets), m_weights(weights) {}

double Portfolio::get_expected_return() const {
    double ret = 0.0;
    for (size_t i = 0; i < m_assets.size(); ++i) {
        ret += m_assets[i].expected_return * m_weights[i];
    }
    return ret;
}

double Portfolio::get_variance(const Eigen::MatrixXd& cov_matrix) const {
    // Math: Variance = W^T * Cov * W
    // In Eigen, matrix multiplication is just the * operator.
    // .transpose() does exactly what it says.
    // The result is a 1x1 matrix, so we use (0,0) to extract the double value.
    Eigen::MatrixXd variance_matrix = m_weights.transpose() * cov_matrix * m_weights;
    return variance_matrix(0, 0); 
}
