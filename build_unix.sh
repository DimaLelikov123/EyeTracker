#!/usr/bin/env bash
# EyeTracker — Unix (macOS / Linux) Setup and Build Script
set -e

echo "=== EyeTracker: Unix Setup & Build ==="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required. Please install Python 3.9+."
    exit 1
fi

# Create virtual environment if not present
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment .venv..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip and install requirements
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Run application test
echo "Verifying application..."
python3 -c "from gui_app import EyeTrackerApp; print('App module loaded successfully!')"

# Optional: Build with PyInstaller
if [ "$1" == "--build" ]; then
    echo "Building standalone binary for $(uname -s)..."
    pyinstaller --noconfirm \
        --name "EyeTracker" \
        --windowed \
        --add-data "assets:assets" \
        --collect-data "customtkinter" \
        --collect-all "mediapipe" \
        run.py
    echo "Build completed in dist/EyeTracker!"
else
    echo "To run the app now: python3 run.py"
    echo "To build a standalone package: ./build_unix.sh --build"
fi
