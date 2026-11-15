import json

import pytest

from scripts.package_manifest import REQUIRED, build_manifest, verify_manifest


def prepare(root):
    for relative in REQUIRED:
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


def test_manifest_detects_missing_entry(tmp_path):
    prepare(tmp_path)
    manifest = build_manifest(tmp_path)
    manifest["files"].pop("app.py", None)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert "app.py" in verify_manifest(tmp_path, path)


def test_manifest_covers_source_tree_and_detects_tamper(tmp_path):
    prepare(tmp_path)
    source = tmp_path / "faro"
    source.mkdir()
    (source / "controller.py").write_text("safe", encoding="utf-8")
    manifest = build_manifest(tmp_path)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    (source / "controller.py").write_text("tampered", encoding="utf-8")
    assert "faro/controller.py" in verify_manifest(tmp_path, path)


@pytest.mark.parametrize("relative", ["fixtures/person.wav", "private/secret.txt"])
def test_manifest_rejects_private_or_audio_material(tmp_path, relative):
    prepare(tmp_path)
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("private", encoding="utf-8")
    with pytest.raises(ValueError):
        build_manifest(tmp_path)
