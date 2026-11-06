import json

import pytest

from scripts.package_manifest import build_manifest, verify_manifest


def prepare(root):
    for relative in ("README.md", "app.py", "fixtures/malla_demo.json", "requirements.txt"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")


def test_manifest_detects_tamper(tmp_path):
    prepare(tmp_path)
    manifest = build_manifest(tmp_path)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert verify_manifest(tmp_path, path) == []
    (tmp_path / "README.md").write_text("tampered", encoding="utf-8")
    assert verify_manifest(tmp_path, path) == ["README.md"]


def test_manifest_requires_essential_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_manifest(tmp_path)
