cmake_minimum_required(VERSION 3.15)
project(RoboAdvisorEngine CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

include(FetchContent)
FetchContent_Declare(
  eigen
  GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
  GIT_TAG        3.4.0
)
FetchContent_MakeAvailable(eigen)

FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG        v2.11.1
)
FetchContent_MakeAvailable(pybind11)

pybind11_add_module(roboadvisor_core Bindings.cpp Portfolio.cpp Optimizer.cpp Backtester.cpp)
target_link_libraries(roboadvisor_core PRIVATE Eigen3::Eigen)

# Standalone C++ Test Executable
add_executable(run_cpp_tests test_optimizer.cpp Portfolio.cpp Optimizer.cpp Backtester.cpp)
target_link_libraries(run_cpp_tests PRIVATE Eigen3::Eigen)

