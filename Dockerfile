# DexHand Data Collector - Docker Configuration
# MuJoCo 24-DOF Five-Finger Dexterous Hand Simulation

FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/logs

# Environment variables
ENV MUJOCO_PY_MJKEY_PATH=/app/mujoco_key/mjkey.txt
ENV MUJOCO_PY_MUJOCO_PATH=/app/mujoco

# Expose port for potential API
EXPOSE 8080

# Default command
CMD ["python", "main.py", "--mode", "demo", "--scene", "assets/scenes/simple_demo.xml"]

# Additional commands available:
# - python main.py --mode validate
# - python main.py --mode train
# - python hardware_validation.py
# - python test_suite.py
# - python real_mujoco_video.py --duration 60
