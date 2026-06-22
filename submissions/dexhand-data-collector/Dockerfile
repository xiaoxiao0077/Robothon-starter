# Dockerfile for DexHand Data Collector
# Supports cross-platform deployment via Docker

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    wget \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data logs models results

# Set environment variables
ENV PYTHONPATH=/app
ENV MUJOCO_GL=osmesa

# Expose ports for WebSocket server
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import mujoco; print('OK')" || exit 1

# Default command
CMD ["python", "main.py", "--mode", "triage"]

# Alternative commands:
# docker run -it dexhand-collector python test_suite.py
# docker run -it dexhand-collector python record_video.py
# docker run -p 8765:8765 dexhand-collector python realtime_interface.py