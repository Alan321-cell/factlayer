"""
FactLayer — Autonomous Fact Knowledge & Reconciliation Engine
Launch script providing single-command startup for the modern Web UI, FastAPI server, and Streamlit.
"""
import sys
import subprocess
import os
import time
from pathlib import Path

def main():
    print("=" * 75)
    print(" 🚀 Starting FactLayer — Autonomous Knowledge Reasoning Engine")
    print("    Multi-Document Intelligence & Fact Reconciliation")
    print("=" * 75)

    base_dir = Path(__file__).resolve().parent

    print(f"[*] Base Directory: {base_dir}")
    print(f"[*] Python Runtime: {sys.executable}")
    print(f"[*] Modern Web Dashboard:     http://127.0.0.1:8000")
    print(f"[*] Interactive API Docs:     http://127.0.0.1:8000/docs")
    print(f"[*] Streamlit UI (Fallback):  http://localhost:8501")
    print("=" * 75)
    print("[*] Launching application services...")

    # Start FastAPI backend (serving modern web app & REST API)
    fastapi_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "api:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000"
    ]

    try:
        subprocess.run(fastapi_cmd, cwd=str(base_dir))
    except KeyboardInterrupt:
        print("\n[+] FactLayer application stopped.")

if __name__ == "__main__":
    main()
