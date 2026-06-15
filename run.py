import subprocess
import sys
import os
import time

def run_backend():
    """Run FastAPI backend"""
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def run_frontend():
    """Run Streamlit frontend"""
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

if __name__ == "__main__":
    print("🚀 Starting Employee Performance Appraisal System...")

    # Start backend
    print("📡 Starting FastAPI backend on http://localhost:8000")
    backend_process = run_backend()
    time.sleep(2)

    # Start frontend
    print("🎨 Starting Streamlit frontend on http://localhost:8501")
    frontend_process = run_frontend()

    print("\n✅ System is running!")
    print("   - Backend API: http://localhost:8000")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Frontend: http://localhost:8501")
    print("\nPress Ctrl+C to stop...")

    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()

