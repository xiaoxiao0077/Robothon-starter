#!/bin/bash
# Cross-platform deployment script for DexHand Data Collector
# Supports Linux, macOS, and Windows (via Git Bash)

set -e  # Exit on error

echo "======================================"
echo "  DexHand Data Collector Deployment"
echo "  UUID: 438a8329-a02c-4fdb-80b5-12bff9d9f69d"
echo "======================================"

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     OS_TYPE=Linux;;
    Darwin*)    OS_TYPE=macOS;;
    MINGW*|MSYS*|CYGWIN*) OS_TYPE=Windows;;
    *)          OS_TYPE="UNKNOWN:${OS}"
esac

echo "Detected OS: ${OS_TYPE}"

# Python version check
echo "Checking Python version..."
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check if Python version is >= 3.8
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "Error: Python 3.8 or higher is required"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
if [ "$OS_TYPE" = "Windows" ]; then
    $PYTHON_CMD -m venv venv
    source venv/Scripts/activate
else
    $PYTHON_CMD -m venv venv
    source venv/bin/activate
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "Running tests..."
$PYTHON_CMD test_suite.py

# Create output directories
echo "Creating output directories..."
mkdir -p data
mkdir -p logs
mkdir -p models
mkdir -p results

# Check MuJoCo installation
echo "Checking MuJoCo installation..."
if $PYTHON_CMD -c "import mujoco" 2>/dev/null; then
    echo "✓ MuJoCo is installed"
else
    echo "⚠ MuJoCo not found. Installing..."
    pip install mujoco
fi

# Run system checks
echo "Running system checks..."
$PYTHON_CMD -c "
import sys
import numpy as np
import time

print('Python version:', sys.version)
print('NumPy version:', np.__version__)
print('NumPy test:', np.random.randn(3))

# Test basic operations
start = time.time()
for _ in range(1000):
    np.random.randn(100)
elapsed = time.time() - start
print(f'Performance test: {elapsed:.4f}s for 1000 random arrays')
"

echo ""
echo "======================================"
echo "  Deployment Complete!"
echo "======================================"
echo ""
echo "To activate the virtual environment:"
if [ "$OS_TYPE" = "Windows" ]; then
    echo "  source venv/Scripts/activate"
else
    echo "  source venv/bin/activate"
fi
echo ""
echo "To run the demo:"
echo "  python main.py --mode triage"
echo ""
echo "To run tests:"
echo "  python test_suite.py"
echo ""
echo "To generate demo video:"
echo "  python record_video.py"
echo ""
echo "======================================"