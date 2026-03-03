#!/bin/bash
echo "=========================================================="
echo "Starting Production Uvicorn Server..."
echo "Binding to 0.0.0.0:5000 with 4 ML worker processes."
echo "=========================================================="

# Exporting default production configurations
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-5000}
export DEBUG_MODE=False

uvicorn main:app --host $HOST --port $PORT --workers 4
