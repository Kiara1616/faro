"""Start Faro's optional tablet/browser console."""

from __future__ import annotations

import os

from faro.web import serve_web


def main() -> None:
    host = os.environ.get("FARO_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("FARO_WEB_PORT", "8765"))
    serve_web(host, port)


if __name__ == "__main__":
    main()
