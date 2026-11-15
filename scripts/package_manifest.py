"""Create/verify a SHA-256 manifest for a local Faro offline package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED = (
    "README.md", "ENTREGA_FARO.md", "app.py", "fixtures/malla_demo.json",
    "requirements.txt", "requirements-voice.txt", "scripts/setup_voice_model.py",
    "scripts/diagnose_offline.py", "scripts/package_manifest.py",
)
FORBIDDEN_SUFFIXES = {".wav", ".mp3", ".mp4", ".sqlite", ".sqlite3", ".log"}
FORBIDDEN_DIRS = {"private", "briefing", "recordings", "audio"}


def validate_package_clean(root: Path) -> None:
    """Fail closed if a delivery tree contains private or disposable material."""
    ignored = {".git", ".venv", "__pycache__", ".pytest_cache", "work", "build", "dist"}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in ignored for part in relative.parts):
            continue
        if path.is_dir() and path.name.casefold() in FORBIDDEN_DIRS:
            raise ValueError(f"Forbidden delivery directory: {relative}")
        if path.is_file() and (path.suffix.casefold() in FORBIDDEN_SUFFIXES
                               or any(part.casefold() in FORBIDDEN_DIRS for part in relative.parts)):
            raise ValueError(f"Forbidden delivery file: {relative}")


def package_files(root: Path) -> list[str]:
    """Return deterministic package files, including source and local assets."""
    names = set(REQUIRED)
    for directory in ("faro", "fixtures", "scripts", "planning", "models"):
        base = root / directory
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if (path.is_file() and not path.is_symlink()
                    and path.suffix not in {".pyc", ".pyo"}
                    and "__pycache__" not in path.parts):
                names.add(path.relative_to(root).as_posix())
    return sorted(names)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def build_manifest(root: str | Path) -> dict[str, object]:
    root = Path(root)
    validate_package_clean(root)
    missing = [item for item in REQUIRED if not (root / item).is_file()]
    if missing:
        raise FileNotFoundError("Missing required package files: " + ", ".join(missing))
    files = {}
    for relative in package_files(root):
        path = root / relative
        files[relative] = digest(path)
    return {"simulation_only": True, "files": files}


def verify_manifest(root: str | Path, manifest: str | Path) -> list[str]:
    expected = json.loads(Path(manifest).read_text(encoding="utf-8"))
    actual = build_manifest(root)["files"]
    expected_files = expected.get("files", {})
    mismatches = sorted({name for name in set(expected_files) | set(actual)
                         if expected_files.get(name) != actual.get(name)})
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera/verifica manifiesto offline Faro.")
    parser.add_argument("root", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        mismatches = verify_manifest(args.root, args.manifest)
        print("OK" if not mismatches else "MISMATCH: " + ", ".join(mismatches))
        return 0 if not mismatches else 1
    args.manifest.write_text(json.dumps(build_manifest(args.root), indent=2), encoding="utf-8")
    print(f"Manifest written: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
