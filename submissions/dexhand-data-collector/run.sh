#!/bin/bash
# DexHand Data Collector - Run Script

echo "======================================"
echo "  DexHand Data Collector"
echo "  UUID: 438a8329-a02c-4fdb-80b5-12bff9d9f69d"
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required. Please install Python first."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run main simulation
echo "Starting simulation..."
python main.py --mode triage

echo "Simulation completed."
