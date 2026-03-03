@echo off
echo ==========================================================
echo Starting Production Uvicorn Server...
echo Binding to 0.0.0.0:5000 with 4 ML worker processes.
echo ==========================================================

uvicorn main:app --host 0.0.0.0 --port 5000 --workers 4
