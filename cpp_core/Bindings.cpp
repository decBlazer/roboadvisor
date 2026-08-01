#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "Optimizer.h"
#include "Backtester.h"

namespace py = pybind11;

// Pybind11 module definition
PYBIND11_MODULE(roboadvisor_core, m) {
    m.doc() = "Robo-Advisor C++ Core Engine"; // Optional module docstring

    // Expose Asset struct
    py::class_<Asset>(m, "Asset")
        .def(py::init<std::string, double, double>(), py::arg("symbol") = "", py::arg("expected_return") = 0.0, py::arg("volatility") = 0.0)
        .def_readwrite("symbol", &Asset::symbol)
        .def_readwrite("expected_return", &Asset::expected_return)
        .def_readwrite("volatility", &Asset::volatility);

    // Expose BacktestResult struct
    py::class_<BacktestResult>(m, "BacktestResult")
        .def_readonly("cagr", &BacktestResult::cagr)
        .def_readonly("sharpe_ratio", &BacktestResult::sharpe_ratio)
        .def_readonly("max_drawdown", &BacktestResult::max_drawdown)
        .def_readonly("portfolio_value_over_time", &BacktestResult::portfolio_value_over_time);

    // Expose Optimizer methods using NumPy buffer maps to ensure safe C/Fortran array memory mapping
    m.def("maximize_sharpe_ratio", [](const std::vector<Asset>& assets, py::array_t<double> cov_arr, double risk_free_rate) {
        py::buffer_info buf = cov_arr.request();
        if (buf.ndim != 2) throw std::runtime_error("Covariance matrix must be 2D");
        Eigen::Map<const Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>> cov_map(
            static_cast<const double*>(buf.ptr), buf.shape[0], buf.shape[1]);
        Eigen::MatrixXd cov = cov_map;
        Eigen::VectorXd w = Optimizer::maximize_sharpe_ratio(assets, cov, risk_free_rate);
        return std::vector<double>(w.data(), w.data() + w.size());
    }, py::arg("assets"), py::arg("cov_matrix"), py::arg("risk_free_rate") = 0.02);

    m.def("calculate_covariance_matrix", [](py::array_t<double> returns_arr) {
        py::buffer_info buf = returns_arr.request();
        if (buf.ndim != 2) throw std::runtime_error("Returns matrix must be 2D");
        Eigen::Map<const Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>> ret_map(
            static_cast<const double*>(buf.ptr), buf.shape[0], buf.shape[1]);
        Eigen::MatrixXd ret = ret_map;
        Eigen::MatrixXd cov = Optimizer::calculate_covariance_matrix(ret);
        
        py::array_t<double> result({cov.rows(), cov.cols()});
        py::buffer_info res_buf = result.request();
        Eigen::Map<Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>> res_map(
            static_cast<double*>(res_buf.ptr), cov.rows(), cov.cols());
        res_map = cov;
        return result;
    }, py::arg("historical_returns"));

    // Expose Backtester method
    m.def("run_backtest", [](py::array_t<double> prices_arr, py::array_t<double> weights_arr, double risk_free_rate) {
        py::buffer_info p_buf = prices_arr.request();
        py::buffer_info w_buf = weights_arr.request();
        
        if (p_buf.ndim != 2) throw std::runtime_error("Historical prices must be a 2D array (n_assets x n_obs)");
        
        Eigen::Map<const Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>> p_map(
            static_cast<const double*>(p_buf.ptr), p_buf.shape[0], p_buf.shape[1]);
        Eigen::MatrixXd prices = p_map;
        
        Eigen::Map<const Eigen::VectorXd> w_map(static_cast<const double*>(w_buf.ptr), w_buf.size);
        Eigen::VectorXd weights = w_map;
        
        return Backtester::run(prices, weights, risk_free_rate);
    }, py::arg("historical_prices"), py::arg("weights"), py::arg("risk_free_rate") = 0.02);
}

