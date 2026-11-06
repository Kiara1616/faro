# Paquete offline verificable

El paquete de demo debe incluir código, guía, malla ficticia y dependencias
fijadas. `scripts/package_manifest.py` genera y verifica SHA-256 sin red:

```powershell
python scripts/package_manifest.py . work/manifest.json
python scripts/package_manifest.py . work/manifest.json --verify
```

Un archivo esencial ausente falla antes de iniciar. Una modificación posterior
produce `MISMATCH`; no se ignora silenciosamente. El modelo Vosk se prepara
antes de desconectar la red y se verifica con `scripts/setup_voice_model.py --check`.

