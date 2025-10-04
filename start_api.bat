@echo off
REM RFQ Tracker API Startup Script
REM This script starts the FastAPI backend server

echo Starting RFQ Tracker API...
cd rfq_scraper
call venv\Scripts\activate.bat
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
pause

