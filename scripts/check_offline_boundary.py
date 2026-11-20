"""Check that the demo runtime has no outbound network client boundary.

The optional web console serves its local HTML interface to a browser; it does
not connect to an external service. The model installer is intentionally the
only module allowed to use urllib and runs before an offline rehearsal.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(
    r"(?:^\s*(?:import\s+(?:socket|requests|httpx|urllib(?:\.|$)|http(?:\.|$)|aiohttp|grpc|ftplib|paramiko|websocket)|from\s+(?:socket|requests|httpx|urllib|http|aiohttp|grpc|ftplib|paramiko|websocket)\s+import)|\b(?:urlopen|urlretrieve|create_connection)\s*\()",
    re.IGNORECASE,
)
ALLOWED = {Path("scripts/setup_voice_model.py")}
SCAN_ROOTS = (Path("app.py"), Path("web_app.py"), Path("faro"), Path("scripts"))


def _python_files(root: Path):
    for relative in SCAN_ROOTS:
        path = root / relative
        if path.is_file():
            yield path
        elif path.is_dir():
            yield from path.rglob("*.py")


def violations(root: Path = ROOT) -> list[dict[str, object]]:
    findings = []
    for path in _python_files(root):
        relative = path.relative_to(root)
        if relative in ALLOWED:
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if FORBIDDEN.search(line):
                findings.append({"file": relative.as_posix(), "line": line_number, "text": line.strip()})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica el límite offline del runtime Faro.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    findings = violations()
    report = {"simulation_only": True, "runtime_network_violations": findings,
              "allowed_installer": "scripts/setup_voice_model.py"}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif findings:
        for finding in findings:
            print(f"{finding['file']}:{finding['line']}: {finding['text']}")
    else:
        print("OK: runtime sin clientes de red; solo se permite el instalador offline previo.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
