"""
Quick start script for FastAPI server
Run this to start the Prescription Processing API
"""

import subprocess
import sys
import os
from pathlib import Path

def run_api():
    """Start the FastAPI server"""
    print("="*70)
    print("PRESCRIPTION PROCESSING API - Fast Start")
    print("="*70)
    
    # Check if main.py exists
    if not Path("main.py").exists():
        print("❌ Error: main.py not found!")
        print("Make sure you're in the Ml-Models directory")
        sys.exit(1)
    
    # Check if requirements installed
    print("\n✓ Checking dependencies...")
    try:
        import fastapi
        import uvicorn
        print("✓ FastAPI and Uvicorn installed")
    except ImportError:
        print("❌ Missing dependencies. Installing...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
    
    print("\n" + "="*70)
    print("Starting API Server...")
    print("="*70)
    
    # Load .env to get dynamic port and host bindings
    host = "127.0.0.1"
    port = "5000"
    try:
        from dotenv import load_dotenv
        load_dotenv()
        host = os.getenv("HOST", host)
        port = os.getenv("PORT", port)
    except ImportError:
        pass
        
    print(f"\n📍 API Running at: http://{host}:{port}")
    print(f"📚 Swagger Docs: http://{host}:{port}/api/docs")
    print(f"📖 ReDoc: http://{host}:{port}/api/redoc")
    print(f"💡 Health Check: http://{host}:{port}/health")
    print("\nPress Ctrl+C to stop the server\n")
    print("="*70 + "\n")
    
    # Run the server
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", host, "--port", port],
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("API Server stopped")
        print("="*70)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_api()
