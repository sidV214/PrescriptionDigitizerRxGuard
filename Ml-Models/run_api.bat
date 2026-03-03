@echo off
REM FastAPI Server Starter for Windows

echo.
echo ========================================================================
echo PRESCRIPTION PROCESSING API - FastAPI Server
echo ========================================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

REM Check if requirements are installed
echo Checking dependencies...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Start the server
echo.
echo Starting FastAPI server...
echo.
echo ========================================================================
echo API Running at: http://localhost:8000
echo.
echo Swagger Docs: http://localhost:8000/api/docs
echo ReDoc: http://localhost:8000/api/redoc
echo Health Check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo ========================================================================
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
