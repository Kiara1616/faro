# Paquete offline verificable

El paquete de demo debe incluir código, guía, malla ficticia y dependencias
fijadas. `scripts/package_manifest.py` genera y verifica SHA-256 sin red:

```powershell
python scripts/package_manifest.py . work/manifest.json
python scripts/package_manifest.py . work/manifest.json --verify
```

El manifiesto cubre los archivos esenciales y recorre el árbol distribuible
(`faro/`, `fixtures/`, `scripts/`, `planning/`, `models/` y archivos raíz). La
carpeta `work/` no se hashea, pero se escanea: si contiene WAV, SQLite, logs o
material privado, la generación falla hasta limpiarla. Así detecta cambios en
el código y en el modelo, no solo en nueve archivos raíz. Un archivo esencial
ausente, añadido o modificado produce `MISMATCH`; no se ignora silenciosamente.
El modelo Vosk se prepara antes de desconectar la red y se verifica con
`scripts/setup_voice_model.py --check`.

