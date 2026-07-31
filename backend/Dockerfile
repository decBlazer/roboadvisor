FROM python:3.11-slim-bullseye

# Install build dependencies for C++ (g++, cmake, git)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy C++ core source code
COPY cpp_core /app/cpp_core

# Build C++ pybind11 module
RUN mkdir -p /app/cpp_core/build && \
    cd /app/cpp_core/build && \
    cmake .. && \
    cmake --build . --config Release

# Copy C++ compiled module to backend directory or python path
RUN cp /app/cpp_core/build/*.so /app/backend/ 2>/dev/null || cp /app/cpp_core/build/Release/*.so /app/backend/ 2>/dev/null || true

# Copy Python backend code
COPY backend /app/backend

WORKDIR /app/backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
