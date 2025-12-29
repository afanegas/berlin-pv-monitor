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

# Record start time
START_TIME=$SECONDS

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

# Save the new CSV temporarily
echo "Saving Temp-Copy of the csv..."
cp solar_berlin_yearly.csv solar_berlin_yearly.csv.tmp

# Fetch latest, reset to remote (discard local history)
echo "Fetching..."
git fetch origin main
echo "Reseting local repository..."
git reset --hard origin/main

# Restore the new CSV
echo "Restoring csv..."
mv solar_berlin_yearly.csv.tmp solar_berlin_yearly.csv

# Now stage and commit the CSV
echo "Stagin and commiting the csv..."
git add solar_berlin_yearly.csv
git commit -m "Auto-update solar data: $(date +'%Y-%m-%d')"

# Push (should work cleanly now)
echo "Pushing..."
git push origin main

# Calculate duration
END_TIME=$SECONDS
DURATION=$((END_TIME - START_TIME))

echo "===================================================="
echo "Finished Successfully: $(date)"
echo "Total Execution Time: $(($DURATION / 60)) min $(($DURATION % 60)) sec"
echo "===================================================="
