"""Remove only disposable local evidence files from a caller-selected folder."""

from __future__ import annotations

import argparse
from pathlib import Path


ALLOWED_SUFFIXES = {".wav", ".sqlite", ".sqlite3", ".log"}


def clean_evidence(folder: str | Path) -> list[str]:
    root = Path(folder).resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    removed = []
    for path in root.iterdir():
        if path.is_file() and path.suffix.casefold() in ALLOWED_SUFFIXES:
            path.unlink()
            removed.append(path.name)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Limpia solo WAV/SQLite/log de una carpeta de evidencia.")
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    print("Eliminados:", ", ".join(clean_evidence(args.folder)) or "ninguno")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
