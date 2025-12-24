#!/bin/bash

################################################################################
# master.sh: Automated MaStR Data Pipeline Orchestrator
#
# DESCRIPTION:
#   This script manages the full end-to-end workflow for Berlin solar data:
#   1. Sets up logging and performs house-keeping (deleting old logs).
#   2. Activates the Python virtual environment.
#   3. Executes the Data Import/Filter script (Import_MaStR.py).
#   4. Executes the Statistical Analysis script (Analysis_MaStR.py).
#   5. Synchronizes results with GitHub.
#
# AUTHOR: afanegas
# VERSION: 1.0.0
# DATE: 2025-12-22
################################################################################

# Move to the project directory automatically (avoid private path in github)
cd "$(dirname "$0")"

# --- CONFIGURATION ---
mkdir -p logs
LOG_FILE="logs/process_log_$(date +'%Y-%m-%d').log"
VENV_PATH="./venv/bin/activate"

# Cleanup: Delete logs older than 30 days
find logs/ -name "process_log_*.log" -type f -mtime +30 -delete

# Start logging everything
exec > >(tee -a "$LOG_FILE") 2>&1

echo "===================================================="
echo "Starting MaStR Automation: $(date)"
echo "===================================================="

# 1. Activate Virtual Environment
if [ -f "$VENV_PATH" ]; then
    source "$VENV_PATH"
else
    echo "Error: Virtual environment not found."
    exit 1
fi

# 2. Run Import Script
echo "Status: Running Import_MaStR.py..."
python3 Import_MaStR.py

# 3. Run Analysis Script
echo "Status: Running Analysis_MaStR.py..."
python3 Analysis_MaStR.py

# 4. Sync with GitHub 
echo "Status: Syncing with GitHub..."
# Get any HTML updates from laptop
git pull --rebase origin main

# Add only the specific results
git add solar_berlin_yearly.csv
git commit -m "Auto-update solar data: $(date +'%Y-%m-%d')"
git push origin main

echo "===================================================="
echo "Finished Successfully: $(date)"
echo "===================================================="
