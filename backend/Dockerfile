FROM python:3.11-slim-bullseye

# Install build dependencies for C++ (g++, cmake, git)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy C++ core source code and Python backend code
COPY cpp_core /app/cpp_core
COPY backend /app/backend

# Build C++ pybind11 module
RUN rm -rf /app/cpp_core/build && \
    mkdir -p /app/cpp_core/build && \
    cd /app/cpp_core/build && \
    cmake .. && \
    cmake --build . --config Release && \
    cp /app/cpp_core/build/*.so /app/backend/ 2>/dev/null || \
    cp /app/cpp_core/build/Release/*.so /app/backend/ 2>/dev/null || true

WORKDIR /app/backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
