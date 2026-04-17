# preview_engine.py
# Live preview engine — spawns generated projects as subprocesses and proxies them.

import os
import socket
import subprocess
import tempfile
import time
import uuid
from urllib.parse import urlsplit

import requests as _requests
from flask import request


# ─────────────────────────────────────────────
# Session store  { session_id: {proc, port} }
# ─────────────────────────────────────────────
_preview_sessions: dict = {}


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _find_free_port(start: int = 5050, end: int = 5150) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port available in range 5050–5150")


def _reap_dead_sessions() -> None:
    dead = [
        sid for sid, entry in _preview_sessions.items()
        if entry["proc"].poll() is not None
    ]
    for sid in dead:
        _preview_sessions.pop(sid, None)


def _kill_session(session_id: str) -> None:
    entry = _preview_sessions.pop(session_id, None)
    if not entry:
        return
    proc = entry.get("proc")
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()
    # Clean up the patched launcher script if present
    launcher = entry.get("launcher")
    if launcher and os.path.isfile(launcher):
        try:
            os.remove(launcher)
        except OSError:
            pass
    log_path = entry.get("log_path")
    if log_path and os.path.isfile(log_path):
        try:
            os.remove(log_path)
        except OSError:
            pass


def _read_preview_log(log_path: str, max_chars: int = 1200) -> str:
    if not log_path or not os.path.isfile(log_path):
        return ""
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read().strip()
    except OSError:
        return ""
    if len(content) > max_chars:
        return content[-max_chars:]
    return content


def _patch_app_for_preview(project_path: str, port: int) -> str:
    """
    Writes a small launcher script next to the generated app.py that:
      - imports the generated app
      - replaces app.run() with the correct host/port and no reloader/debugger
    Returns the path to the launcher script.

    This avoids touching the user's generated app.py at all.
    """
    launcher_src = f"""
import sys
import os

# Make sure the project root is on the path
sys.path.insert(0, {repr(project_path)})
os.chdir({repr(project_path)})

# ── Monkey-patch Flask's run() before importing the generated app ──
import flask as _flask
_original_run = _flask.Flask.run

def _patched_run(self, host=None, port=None, debug=None, **kwargs):
    # Always use our chosen host/port, never the reloader
    kwargs.pop("use_reloader", None)
    kwargs.pop("threaded", None)
    _original_run(
        self,
        host="127.0.0.1",
        port={port},
        debug=False,
        use_reloader=False,
        threaded=True,
        **kwargs,
    )

_flask.Flask.run = _patched_run

# ── Now import and run the generated app ──
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("generated_app", {repr(os.path.join(project_path, "app.py"))})
_mod  = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_app = getattr(_mod, "app", None)
if _app is None and hasattr(_mod, "create_app"):
    _app = _mod.create_app()

if _app is None:
    raise RuntimeError("Generated project did not expose a Flask app.")

_app.run()
"""
    fd, launcher_path = tempfile.mkstemp(suffix="_preview_launcher.py", prefix="preview_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(launcher_src)
    return launcher_path


# ─────────────────────────────────────────────
# Public API  (called from route handlers)
# ─────────────────────────────────────────────

def start_preview(project_path: str) -> dict:
    """
    Spawns the generated project on a free port via a patched launcher.
    Returns { session_id, preview_url, proxy_url } or raises ValueError/RuntimeError.
    """
    _reap_dead_sessions()

    if not project_path or not os.path.isdir(project_path):
        raise ValueError("Invalid project_path")

    app_py = os.path.join(project_path, "app.py")
    if not os.path.isfile(app_py):
        raise ValueError("No app.py found in project")

    port = _find_free_port()
    launcher_path = _patch_app_for_preview(project_path, port)

    env = os.environ.copy()
    env["FLASK_RUN_HOST"] = "127.0.0.1"
    env["FLASK_RUN_PORT"] = str(port)
    # Avoid inheriting Werkzeug dev-server socket state from the parent Flask process.
    env.pop("WERKZEUG_SERVER_FD", None)
    env.pop("WERKZEUG_RUN_MAIN", None)
    env.pop("FLASK_RUN_FROM_CLI", None)

    log_fd, log_path = tempfile.mkstemp(suffix="_preview.log", prefix="preview_")
    os.close(log_fd)
    log_handle = open(log_path, "w", encoding="utf-8")

    try:
        proc = subprocess.Popen(
            ["python", launcher_path],
            cwd=project_path,
            env=env,
            stdout=log_handle,
            stderr=log_handle,
        )
    finally:
        log_handle.close()

    # Wait up to 5 s for the port to become reachable
    deadline = time.time() + 5
    alive = False
    while time.time() < deadline:
        if proc.poll() is not None:
            break                          # process already died
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.3):
                alive = True
                break
        except OSError:
            time.sleep(0.3)

    if not alive or proc.poll() is not None:
        try:
            os.remove(launcher_path)
        except OSError:
            pass
        error_details = _read_preview_log(log_path)
        try:
            os.remove(log_path)
        except OSError:
            pass
        message = "Preview process failed to start. Check the generated app for import errors."
        if error_details:
            message += f" Details: {error_details}"
        raise RuntimeError(
            message
        )

    session_id = uuid.uuid4().hex
    _preview_sessions[session_id] = {
        "proc": proc,
        "port": port,
        "launcher": launcher_path,
        "log_path": log_path,
    }

    return {
        "session_id": session_id,
        "preview_url": f"http://127.0.0.1:{port}",
        "proxy_url": f"/preview/proxy/{session_id}/",
    }


def stop_preview(session_id: str) -> None:
    """Terminates the subprocess for the given session."""
    _kill_session(session_id)


def proxy_preview(session_id: str, subpath: str):
    """
    Forwards the current Flask request to the running subprocess and
    rewrites HTML so relative URLs stay within the proxy path.
    Must be called from inside a Flask request context.
    """
    entry = _preview_sessions.get(session_id)
    if not entry:
        return None, "Preview session not found or expired.", 404

    port = entry["port"]
    target_url = f"http://127.0.0.1:{port}/{subpath}"
    if request.query_string:
        target_url += "?" + request.query_string.decode()

    try:
        resp = _requests.request(
            method=request.method,
            url=target_url,
            headers={
                k: v for k, v in request.headers
                if k.lower() not in ("host", "content-length")
            },
            data=request.get_data(),
            allow_redirects=False,
            timeout=8,
        )
    except _requests.exceptions.ConnectionError:
        return None, "Preview app is not reachable yet — it may still be starting.", 502
    except _requests.exceptions.Timeout:
        return None, "Preview app timed out.", 504

    content = resp.content
    content_type = resp.headers.get("Content-Type", "")

    if "text/html" in content_type:
        prefix = f"/preview/proxy/{session_id}".encode()
        content = content.replace(b'href="/', b'href="' + prefix + b"/")
        content = content.replace(b'src="/',  b'src="'  + prefix + b"/")
        content = content.replace(b'action="/', b'action="' + prefix + b"/")

    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}

    location = headers.get("Location")
    if location:
        parsed = urlsplit(location)
        if not parsed.scheme and not parsed.netloc and location.startswith("/"):
            headers["Location"] = f"/preview/proxy/{session_id}{location}"
        elif parsed.hostname in {"127.0.0.1", "localhost"} and parsed.port == port:
            headers["Location"] = f"/preview/proxy/{session_id}{parsed.path or '/'}"
            if parsed.query:
                headers["Location"] += f"?{parsed.query}"

    return content, headers, resp.status_code
