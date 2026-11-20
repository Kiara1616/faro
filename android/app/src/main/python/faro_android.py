"""Start Faro's bundled simulator on this Android device only."""

from __future__ import annotations

from http.server import ThreadingHTTPServer
import os
from pathlib import Path
import threading

from faro.web import WebConsole, create_request_handler


_lock = threading.Lock()
_server: ThreadingHTTPServer | None = None


def start(data_dir: str | None = None) -> str:
    """Return the local URL, reusing the server after an Activity recreation."""
    global _server
    with _lock:
        if _server is None:
            bundle_root = Path(__file__).resolve().parent
            audit_root = Path(data_dir) if data_dir else Path(os.environ["HOME"])
            audit_root.mkdir(parents=True, exist_ok=True)
            audit_path = audit_root / "faro-web-audit.sqlite3"
            console = WebConsole.create(root=bundle_root, audit_path=audit_path)
            handler = create_request_handler(console, bundle_root / "web")
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            server.daemon_threads = True
            thread = threading.Thread(target=server.serve_forever, name="faro-local", daemon=True)
            thread.start()
            _server = server
        return f"http://127.0.0.1:{_server.server_port}/"
