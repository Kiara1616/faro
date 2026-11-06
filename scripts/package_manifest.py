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


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def build_manifest(root: str | Path) -> dict[str, object]:
    root = Path(root)
    missing = [item for item in REQUIRED if not (root / item).is_file()]
    if missing:
        raise FileNotFoundError("Missing required package files: " + ", ".join(missing))
    files = {}
    for relative in REQUIRED:
        path = root / relative
        files[relative] = digest(path)
    return {"simulation_only": True, "files": files}


def verify_manifest(root: str | Path, manifest: str | Path) -> list[str]:
    expected = json.loads(Path(manifest).read_text(encoding="utf-8"))
    actual = build_manifest(root)["files"]
    expected_files = expected.get("files", {})
    mismatches = [name for name in REQUIRED if expected_files.get(name) != actual.get(name)]
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
