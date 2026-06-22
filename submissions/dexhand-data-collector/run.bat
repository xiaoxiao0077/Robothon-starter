@echo off
REM DexHand Data Collector - Run Script for Windows
REM UUID: 438a8329-a02c-4fdb-80b5-12bff9d9f69d

echo ======================================
echo   DexHand Data Collector
echo   UUID: 438a8329-a02c-4fdb-80b5-12bff9d9f69d
echo ======================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is required. Please install Python first.
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run main simulation
echo Starting simulation...
python main.py --mode triage

echo Simulation completed.
pause
