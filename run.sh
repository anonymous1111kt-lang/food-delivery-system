#!/usr/bin/env bash
# QuickBite - Online Food Delivery Management System Launch Script

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    venv/bin/pip install -r requirements.txt
fi

echo "Starting QuickBite Online Food Delivery Management System..."
echo "Web URL: http://localhost:5001"
venv/bin/python app.py
