"""Install the official small Spanish Vosk model for the Faro demo.

The Vosk model catalog lists this model as Apache 2.0, but does not publish
an archive checksum. The installer prints the downloaded SHA-256 for audit;
an independently obtained digest can be enforced with --sha256.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import stat
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


MODEL_NAME = "vosk-model-small-es-0.42"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = PROJECT_ROOT / "models" / MODEL_NAME
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_EXTRACTED_BYTES = 500 * 1024 * 1024
REQUIRED_FILES = ("am/final.mdl", "conf/model.conf", "graph/HCLr.fst", "graph/Gr.fst")


def model_is_complete(path: Path) -> bool:
    return path.is_dir() and all((path / part).is_file() for part in REQUIRED_FILES)


def _download(url: str, archive: Path) -> str:
    digest = hashlib.sha256()
    total = 0
    with urllib.request.urlopen(url, timeout=30) as response, archive.open("wb") as output:
        while block := response.read(1024 * 1024):
            total += len(block)
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("El archivo del modelo supera el límite de 100 MB.")
            digest.update(block)
            output.write(block)
    return digest.hexdigest()


def _safe_extract(archive: Path, staging: Path) -> Path:
    model_dir = staging / MODEL_NAME
    total = 0
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            name = member.filename
            if "\\" in name or name.startswith("/"):
                raise ValueError(f"Ruta no permitida dentro del ZIP: {name}")
            parts = PurePosixPath(name).parts
            if not parts or parts[0] != MODEL_NAME or any(part in ("", ".", "..") for part in parts):
                raise ValueError(f"Ruta fuera del modelo dentro del ZIP: {name}")
            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError(f"Enlace simbólico no permitido dentro del ZIP: {name}")
            total += member.file_size
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError("El modelo descomprimido supera el límite de 500 MB.")

            destination = staging.joinpath(*parts)
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)
    if not model_is_complete(model_dir):
        raise ValueError("El ZIP no contiene los archivos esenciales de un modelo Vosk.")
    return model_dir


def install_model(
    target: Path = DEFAULT_TARGET,
    *,
    url: str = MODEL_URL,
    expected_sha256: str | None = None,
) -> tuple[Path, str | None]:
    """Install atomically; return (model path, download SHA-256 or None if present)."""
    target = Path(target)
    if model_is_complete(target):
        return target, None
    if target.exists():
        raise FileExistsError(f"La carpeta de destino existe, pero el modelo está incompleto: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vosk-setup-", dir=target.parent) as temp:
        staging = Path(temp)
        archive = staging / "model.zip"
        actual_sha256 = _download(url, archive)
        if expected_sha256 and actual_sha256.lower() != expected_sha256.lower():
            raise ValueError(f"SHA-256 no coincide: se obtuvo {actual_sha256}")
        model_dir = _safe_extract(archive, staging)
        model_dir.rename(target)
    return target, actual_sha256


def main() -> int:
    parser = argparse.ArgumentParser(description="Instala el modelo Vosk español pequeño de Faro.")
    parser.add_argument("--check", action="store_true", help="Solo verifica la instalación local; no descarga.")
    parser.add_argument("--sha256", help="SHA-256 esperado de una fuente confiable, si se dispone de él.")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET, help="Carpeta destino del modelo.")
    args = parser.parse_args()

    if args.check:
        if model_is_complete(args.target):
            print(f"Modelo instalado: {args.target}")
            return 0
        print(f"Modelo ausente o incompleto: {args.target}", file=sys.stderr)
        return 1

    try:
        path, sha256 = install_model(args.target, expected_sha256=args.sha256)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"No se pudo instalar el modelo: {exc}", file=sys.stderr)
        return 1
    print(f"Modelo listo: {path}")
    if sha256:
        print(f"SHA-256 del ZIP descargado: {sha256}")
    else:
        print("El modelo ya estaba instalado; no se descargó nuevamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
