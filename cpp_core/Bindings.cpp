#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>

#include "Optimizer.h"
#include "Backtester.h"

namespace py = pybind11;

// Pybind11 module definition
PYBIND11_MODULE(roboadvisor_core, m) {
    m.doc() = "Robo-Advisor C++ Core Engine"; // Optional module docstring

    // Expose Asset struct
    py::class_<Asset>(m, "Asset")
        .def(py::init<std::string, double, double>())
        .def_readwrite("symbol", &Asset::symbol)
        .def_readwrite("expected_return", &Asset::expected_return)
        .def_readwrite("volatility", &Asset::volatility);

    // Expose BacktestResult struct
    py::class_<BacktestResult>(m, "BacktestResult")
        .def_readonly("cagr", &BacktestResult::cagr)
        .def_readonly("sharpe_ratio", &BacktestResult::sharpe_ratio)
        .def_readonly("max_drawdown", &BacktestResult::max_drawdown)
        .def_readonly("portfolio_value_over_time", &BacktestResult::portfolio_value_over_time);

    // Expose Optimizer methods (static methods exposed as free functions)
    m.def("maximize_sharpe_ratio", &Optimizer::maximize_sharpe_ratio, 
          "Calculate tangency portfolio weights",
          py::arg("assets"), py::arg("cov_matrix"), py::arg("risk_free_rate") = 0.02);

    m.def("calculate_covariance_matrix", &Optimizer::calculate_covariance_matrix,
          "Calculate covariance matrix from historical returns",
          py::arg("historical_returns"));

    // Expose Backtester method
    m.def("run_backtest", &Backtester::run,
          "Simulate portfolio performance over time",
          py::arg("historical_prices"), py::arg("weights"), py::arg("risk_free_rate") = 0.02);
}
