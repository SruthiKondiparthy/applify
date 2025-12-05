#!/usr/bin/env python3
import subprocess
import time
import webbrowser
import sys
import os
import socket
import argparse
import threading

# -------- COLOR OUTPUT -----------------------------------------
class Color:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"

def info(msg): print(f"{Color.BLUE}ℹ {msg}{Color.END}")
def success(msg): print(f"{Color.GREEN}✔ {msg}{Color.END}")
def warn(msg): print(f"{Color.YELLOW}⚠ {msg}{Color.END}")
def error(msg): print(f"{Color.RED}✖ {msg}{Color.END}")

# -------- PORT CHECK --------------------------------------------
def find_free_port(start_port):
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1

# -------- LOGGING SETUP -----------------------------------------
def ensure_log_dir():
    if not os.path.exists("logs"):
        os.makedirs("logs")

ensure_log_dir()

# -------- START PROCESSES ----------------------------------------
def run_backend(port, watch_mode):
    log_file = open("logs/backend.log", "w")
    success(f"Starting Backend (FastAPI) on port {port}...")

    cmd = [
        "uvicorn", "api.main:app",
        "--host", "0.0.0.0",
        "--port", str(port)
    ]

    if watch_mode:
        cmd.append("--reload")

    return subprocess.Popen(cmd, stdout=log_file, stderr=log_file)

def run_frontend(port):
    log_file = open("logs/frontend.log", "w")
    success(f"Starting Frontend (Streamlit) on port {port}...")

    cmd = ["streamlit", "run", "ui/main.py", "--server.port", str(port)]
    return subprocess.Popen(cmd, stdout=log_file, stderr=log_file)

# -------- WATCH MODE (AUTO RESTART) ------------------------------
def watch_and_restart(cmd, label):
    """
    Simple file watcher using mtime to restart on changes.
    """
    import time

    last_mtimes = {}

    while True:
        time.sleep(1)
        changed = False

        for root, _, files in os.walk("."):
            for f in files:
                if f.endswith((".py", ".txt")):
                    path = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(path)
                    except:
                        continue
                    if path not in last_mtimes:
                        last_mtimes[path] = mtime
                    elif last_mtimes[path] != mtime:
                        changed = True
                        last_mtimes[path] = mtime

        if changed:
            warn(f"Detected code change → restarting {label}...")
            return True

# -------- MAIN ----------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true",
                        help="Enable auto-restart on file changes")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    backend_port = find_free_port(8000)
    frontend_port = find_free_port(8501)

    while True:
        backend = run_backend(backend_port, args.watch)
        time.sleep(2)

        frontend = run_frontend(frontend_port)
        time.sleep(2)

        webbrowser.open(f"http://localhost:{frontend_port}")

        success("Applify is running!")
        info(f"Backend:  http://localhost:{backend_port}/docs")
        info(f"Frontend: http://localhost:{frontend_port}")

        if args.watch:
            restarted_backend = watch_and_restart("backend", "backend/frontend")

            if restarted_backend:
                warn("Restarting both services...")
                backend.terminate()
                frontend.terminate()
                time.sleep(1)
                continue
        else:
            try:
                backend.wait()
                frontend.wait()
            except KeyboardInterrupt:
                warn("Shutting down...")
                backend.terminate()
                frontend.terminate()
                sys.exit(0)

        break

if __name__ == "__main__":
    main()
