#pragma once
#include <vector>
#include <string>
#include <Eigen/Dense>

// In Java, this would just be a Class. In C++, we often use 'struct' for simple data containers.
struct Asset {
    std::string symbol;
    double expected_return;
    double volatility;

    Asset(std::string s = "", double e = 0.0, double v = 0.0)
        : symbol(std::move(s)), expected_return(e), volatility(v) {}
};

class Portfolio {
public:
    // Constructors in C++ work similarly to Java
    Portfolio(const std::vector<Asset>& assets, const Eigen::VectorXd& weights);

    // 'const' at the end means this method doesn't modify the object (good practice in C++)
    double get_expected_return() const;
    
    // We'll pass the covariance matrix as an Eigen Matrix to calculate variance
    double get_variance(const Eigen::MatrixXd& cov_matrix) const;

private:
    std::vector<Asset> m_assets;
    
    // We use Eigen::VectorXd for math vectors, instead of std::vector
    Eigen::VectorXd m_weights; 
};
