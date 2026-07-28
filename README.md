# Robo-Advisor — C++ / Python / Next.js

A high-performance Robo-Advisor portfolio engine that calculates optimal asset allocations using **Modern Portfolio Theory (MPT)**. Built with a **C++ Eigen core** exposed to a **FastAPI (Python)** backend via **pybind11**, paired with a modern **Next.js** dashboard.

---

## 🏛️ Architecture

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Next.js UI    │ ────> │ FastAPI Backend │ ────> │  C++ Core Engine│
│   (Dashboard)   │ <──── │   (Python API)  │ <──── │(pybind11 + Eigen)│
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

* **C++ Core Engine (`cpp_core/`)**: Eigen-based linear algebra solver for mean-variance optimization (tangency portfolio) and historical backtesting calculations.
* **Python API (`backend/`)**: Orchestrates data ingestion from `yfinance`, handles risk profile scoring, and bridges calls into C++. Includes a pure Python/NumPy baseline fallback.
* **Next.js Frontend (`frontend/`)**: Modern dark-mode dashboard for risk profiling, allocation visualizer, and backtest metrics.

---

## 🚀 How to Run Locally

### Option A: Using Docker (Recommended & Easiest)
This automatically compiles the C++ pybind11 module inside a Linux build container.

```bash
# Clone and navigate to repo root
cd roboadvisor

# Build and start services
docker-compose up --build
```
* **Frontend**: `http://localhost:3000`
* **FastAPI Backend**: `http://localhost:8000`
* **API Docs**: `http://localhost:8000/docs`

---

### Option B: Local Python + Frontend (Without C++ Compilation)
If you don't have C++ build tools installed locally, the backend automatically uses the **Python NumPy baseline engine**.

#### 1. Start Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### 2. Start Frontend:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

### Option C: Compiling C++ Engine Locally

#### Requirements:
* CMake (v3.15+)
* C++17 compatible compiler (MSVC on Windows, GCC/Clang on Linux/macOS)

```bash
cd cpp_core
mkdir build && cd build
cmake ..
cmake --build . --config Release

# Copy compiled .so / .pyd file to backend/
cp roboadvisor_core* ../../backend/
```

---

## 💡 Key Technical Highlights for Interviews

1. **Why C++?**: Closed-form matrix operations ($W = \Sigma^{-1} \cdot R_{excess}$) executed in C++ compiled code vs iterative Python loops.
2. **pybind11 Zero-Copy Interop**: `pybind11/eigen.h` enables direct, zero-copy conversion between NumPy arrays and Eigen matrix types.
3. **Resilience & Fallback Architecture**: The API seamlessly detects if the compiled native C++ binary is present, falling back to a pure SciPy/NumPy baseline without breaking the UI.
