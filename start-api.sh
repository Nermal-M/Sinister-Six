#!/bin/bash
# Railway Complaint System - Startup Script (Linux/Mac)
# This script starts the Flask API for complaint classification

echo ""
echo "========================================"
echo "Railway Complaint System - Auto Classification"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org"
    exit 1
fi

echo "Python version:"
python3 --version

echo ""
echo "Step 1: Checking Python dependencies..."
python3 -m pip list | grep -E "Flask|transformers|torch" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo ""
    echo "Step 2: Installing dependencies..."
    echo "(This may take 5-10 minutes on first run)"
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo ""
echo "Step 3: Starting Flask API Server..."
echo ""
echo "The API server will run on: http://127.0.0.1:5000"
echo ""
echo "IMPORTANT:"
echo "- Keep this window open while using the system"
echo "- Open register-complaint.html in your browser"
echo "- The system will auto-classify complaints when you type"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 api.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to start API server"
    echo "Check the error messages above"
    exit 1
fi
