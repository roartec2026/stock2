#!/bin/bash
# Linux/Mac shell script launcher for Stock ROARSTAR Dashboard
# Checks and installs packages, then runs the dashboard

echo "============================================================"
echo "Stock ROARSTAR Analysis Admin Dashboard - Launcher"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    echo "Please install Python 3.7 or higher"
    exit 1
fi

echo "Python found: $(python3 --version)"
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip3 is not available!"
    exit 1
fi

echo "Checking and installing required packages..."
echo ""

# Install packages from requirements.txt
pip3 install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo ""
    echo "WARNING: Some packages may not have installed correctly."
    echo "You can try installing manually: pip3 install -r requirements.txt"
    echo ""
    read -p "Press enter to continue anyway..."
fi

echo ""
echo "============================================================"
echo "Starting Dashboard..."
echo "============================================================"
echo ""
echo "The dashboard will open in your default web browser."
echo "If it doesn't open automatically, go to: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

# Run Streamlit dashboard
streamlit run dashboard.py

