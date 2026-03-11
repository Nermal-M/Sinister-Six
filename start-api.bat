@echo off
REM Railway Complaint System - Startup Script
REM This script starts the Flask API for complaint classification

echo.
echo ========================================
echo Railway Complaint System - Auto Classification
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

echo Step 1: Checking Python dependencies...
python -m pip list | findstr "Flask transformers torch" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Step 2: Installing dependencies...
    echo (This may take 5-10 minutes on first run)
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Step 3: Starting Flask API Server...
echo.
echo The API server will run on: http://127.0.0.1:5000
echo.
echo IMPORTANT:
echo - Keep this window open while using the system
echo - Open register-complaint.html in your browser
echo - The system will auto-classify complaints when you type
echo.
echo Press Ctrl+C to stop the server
echo.

python api.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start API server
    echo Check the error messages above
    pause
    exit /b 1
)
