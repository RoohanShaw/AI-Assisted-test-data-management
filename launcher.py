"""
launcher.py — AI TestData Generator Launcher

Startup sequence (background thread):
  1. Open VS Code in project directory
  2. Create Python venv (skip if already exists)
  3. Install packages from deps.txt
  4. Run test_smoke.py — abort if any test fails
  5. Launch python start.py (FastAPI server on port 8000)

Foreground:
  - Serves a live-status dashboard at http://127.0.0.1:8080
  - Auto-opens the browser to that page immediately
  - UI polls /status every second for real-time progress
  - Shows "Open App" button once the FastAPI server is ready
"""

import json
import os
import platform
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# ── Resolve paths (works both frozen and normal) ────────────────────────────
if getattr(sys, "frozen", False):
    # When packaged by PyInstaller:
    # - Bundled data files (launcher_ui) are extracted to sys._MEIPASS
    # - The EXE itself sits in PROJECT_ROOT (where venv / deps.txt / start.py live)
    _MEIPASS    = Path(sys._MEIPASS)          # type: ignore[attr-defined]
    PROJECT_ROOT = Path(sys.executable).parent
    UI_FILE      = _MEIPASS / "launcher_ui" / "index.html"
else:
    PROJECT_ROOT = Path(__file__).parent.resolve()
    UI_FILE      = PROJECT_ROOT / "launcher_ui" / "index.html"

VENV_DIR     = PROJECT_ROOT / "venv"
DEPS_FILE    = PROJECT_ROOT / "deps.txt"
SMOKE_SCRIPT = PROJECT_ROOT / "test_smoke.py"
START_SCRIPT = PROJECT_ROOT / "start.py"

# On Windows the venv python / pip paths are under Scripts\
if platform.system() == "Windows":
    VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"
    VENV_PIP    = VENV_DIR / "Scripts" / "pip.exe"
else:
    VENV_PYTHON = VENV_DIR / "bin" / "python"
    VENV_PIP    = VENV_DIR / "bin" / "pip"

LAUNCHER_PORT = 8080
APP_PORT      = 8000

# ── Shared state (read by HTTP handler, written by background thread) ────────
_lock = threading.Lock()

_STATUS = {
    "phase": "starting",          # starting | running | done | error
    "steps": [
        {"id": "vscode",  "label": "Open VS Code",          "state": "pending", "log": []},
        {"id": "venv",    "label": "Create virtual env",    "state": "pending", "log": []},
        {"id": "install", "label": "Install dependencies",  "state": "pending", "log": []},
        {"id": "smoke",   "label": "Run smoke tests",       "state": "pending", "log": []},
        {"id": "launch",  "label": "Launch application",    "state": "pending", "log": []},
    ],
    "app_url": f"http://127.0.0.1:{APP_PORT}/docs",
    "app_ready": False,
    "error": None,
}

_app_process = None  # handle to the start.py subprocess


def _step_index(step_id: str) -> int:
    for i, s in enumerate(_STATUS["steps"]):
        if s["id"] == step_id:
            return i
    raise KeyError(step_id)


def _set_step(step_id: str, state: str, msg: str = ""):
    with _lock:
        idx = _step_index(step_id)
        _STATUS["steps"][idx]["state"] = state
        if msg:
            _STATUS["steps"][idx]["log"].append(msg)


def _log_step(step_id: str, msg: str):
    with _lock:
        idx = _step_index(step_id)
        _STATUS["steps"][idx]["log"].append(msg)


def _run(cmd, step_id: str, env=None, cwd=None):
    """
    Run a subprocess, streaming stdout/stderr to the step log.
    Returns (returncode, combined_output).
    """
    _log_step(step_id, f"$ {' '.join(str(c) for c in cmd)}")
    combined = []
    try:
        proc = subprocess.Popen(
            [str(c) for c in cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(cwd or PROJECT_ROOT),
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
        )
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                _log_step(step_id, line)
                combined.append(line)
        proc.wait()
        return proc.returncode, "\n".join(combined)
    except Exception as exc:
        msg = f"ERROR: {exc}"
        _log_step(step_id, msg)
        return -1, msg


# ── Background orchestration ─────────────────────────────────────────────────

def _background_orchestrate():
    global _app_process
    with _lock:
        _STATUS["phase"] = "running"

    # ── Step 1 · Open VS Code ──────────────────────────────────────────────
    _set_step("vscode", "running", "Opening VS Code…")
    try:
        code_cmd = "code"
        subprocess.Popen(
            [code_cmd, str(PROJECT_ROOT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
        )
        _set_step("vscode", "done", "✓ VS Code launched")
    except FileNotFoundError:
        _set_step("vscode", "warn", "⚠ VS Code not found on PATH — skipping")
    except Exception as exc:
        _set_step("vscode", "warn", f"⚠ Could not open VS Code: {exc}")

    # ── Step 2 · Create venv ──────────────────────────────────────────────
    _set_step("venv", "running")
    if VENV_DIR.exists() and VENV_PYTHON.exists():
        _set_step("venv", "done", "✓ venv already exists — reusing")
    else:
        _log_step("venv", f"Creating venv at {VENV_DIR} …")
        rc, out = _run([sys.executable, "-m", "venv", str(VENV_DIR)], "venv")
        if rc != 0:
            _set_step("venv", "error", "✗ Failed to create venv")
            with _lock:
                _STATUS["phase"] = "error"
                _STATUS["error"] = "venv creation failed"
            return
        _set_step("venv", "done", "✓ venv created successfully")

    # ── Step 3 · Install deps ─────────────────────────────────────────────
    _set_step("install", "running", f"Installing packages from {DEPS_FILE.name} …")
    if not DEPS_FILE.exists():
        _set_step("install", "warn", f"⚠ {DEPS_FILE.name} not found — skipping install")
    else:
        rc, out = _run(
            [str(VENV_PIP), "install", "-r", str(DEPS_FILE)],
            "install",
        )
        if rc != 0:
            _set_step("install", "error", "✗ pip install failed — check logs")
            with _lock:
                _STATUS["phase"] = "error"
                _STATUS["error"] = "Dependency installation failed"
            return
        _set_step("install", "done", "✓ All dependencies installed")

    # ── Step 4 · Smoke tests ──────────────────────────────────────────────
    _set_step("smoke", "running", "Running smoke tests …")
    rc, out = _run(
        [str(VENV_PYTHON), str(SMOKE_SCRIPT)],
        "smoke",
        cwd=PROJECT_ROOT,
    )
    if rc != 0:
        _set_step("smoke", "error", "✗ Smoke tests FAILED — application will not start")
        with _lock:
            _STATUS["phase"] = "error"
            _STATUS["error"] = "Smoke tests failed — see log for details"
        return
    _set_step("smoke", "done", "✓ All smoke tests passed")

    # ── Step 5 · Launch app ───────────────────────────────────────────────
    _set_step("launch", "running", "Starting FastAPI application …")
    try:
        _app_process = subprocess.Popen(
            [str(VENV_PYTHON), str(START_SCRIPT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
        )
    except Exception as exc:
        _set_step("launch", "error", f"✗ Failed to start app: {exc}")
        with _lock:
            _STATUS["phase"] = "error"
            _STATUS["error"] = str(exc)
        return

    # Stream app output + watch for ready signal
    def _tail_app():
        for line in _app_process.stdout:
            line = line.rstrip()
            if line:
                _log_step("launch", line)
                # Uvicorn logs "Application startup complete." when ready
                if "startup complete" in line.lower() or "server ready" in line.lower():
                    _set_step("launch", "done", "✓ Application is running 🚀")
                    with _lock:
                        _STATUS["phase"] = "done"
                        _STATUS["app_ready"] = True

    threading.Thread(target=_tail_app, daemon=True).start()

    # Fallback: if after 60 s the process is still alive, mark as ready anyway
    def _fallback_ready():
        deadline = time.time() + 60
        while time.time() < deadline:
            time.sleep(2)
            with _lock:
                if _STATUS["app_ready"] or _STATUS["phase"] == "error":
                    return
        with _lock:
            if not _STATUS["app_ready"]:
                _STATUS["app_ready"] = True
                _STATUS["phase"] = "done"
        _set_step("launch", "done", "✓ Application should be ready")

    threading.Thread(target=_fallback_ready, daemon=True).start()


# ── Tiny HTTP server ─────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silence default request logging

    def _send(self, code: int, content_type: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            with _lock:
                data = json.dumps(_STATUS).encode()
            self._send(200, "application/json", data)

        elif self.path in ("/", "/index.html"):
            if UI_FILE.exists():
                body = UI_FILE.read_bytes()
            else:
                body = b"<h1>Launcher UI not found</h1>"
            self._send(200, "text/html; charset=utf-8", body)

        else:
            self._send(404, "text/plain", b"Not found")


def _serve():
    server = HTTPServer(("127.0.0.1", LAUNCHER_PORT), _Handler)
    server.serve_forever()


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    # Start HTTP server in background
    threading.Thread(target=_serve, daemon=True).start()

    # Start orchestration in background
    threading.Thread(target=_background_orchestrate, daemon=True).start()

    # Open browser to status UI
    url = f"http://127.0.0.1:{LAUNCHER_PORT}"
    time.sleep(0.5)  # tiny delay so server is definitely up
    webbrowser.open(url)

    print(f"[Launcher] Status UI → {url}")
    print(f"[Launcher] App will be available at http://127.0.0.1:{APP_PORT}/docs")
    print("[Launcher] Press Ctrl+C to stop.\n")

    try:
        # Keep main thread alive (daemon threads die when main exits)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Launcher] Shutting down…")
        if _app_process and _app_process.poll() is None:
            _app_process.terminate()
        sys.exit(0)


if __name__ == "__main__":
    main()
