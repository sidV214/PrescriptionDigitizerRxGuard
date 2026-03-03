#!/bin/bash
# FastAPI Server Starter for macOS/Linux

echo ""
echo "========================================================================"
echo "PRESCRIPTION PROCESSING API - FastAPI Server"
echo "========================================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    echo "Then: source venv/bin/activate"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if requirements are installed
echo "Checking dependencies..."
python3 -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Start the server
echo ""
echo "Starting FastAPI server..."
echo ""
echo "========================================================================"
echo "✓ API Running at: http://localhost:8000"
echo ""
echo "📚 Swagger Docs: http://localhost:8000/api/docs"
echo "📖 ReDoc: http://localhost:8000/api/redoc"
echo "💡 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================================================"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
