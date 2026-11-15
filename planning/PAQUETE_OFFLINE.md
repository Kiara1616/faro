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
ausente, añadido o modificado dentro del árbol distribuible produce `MISMATCH`;
`work/` y directorios de desarrollo se excluyen del hash, pero `work/` se
escanea para rechazar audio, SQLite, logs o material privado antes de entregar.
No se ignora silenciosamente un cambio en código, fixtures, documentación,
scripts o modelo.
El procedimiento de preparación, hash y transferencia del modelo está en
`planning/MODELO_VOSK_OFFLINE.md`. Se verifica con
`scripts/setup_voice_model.py --check` antes de desconectar la red.

