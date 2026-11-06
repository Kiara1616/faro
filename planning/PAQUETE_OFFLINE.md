# Paquete offline verificable

El paquete de demo debe incluir código, guía, malla ficticia y dependencias
fijadas. `scripts/package_manifest.py` genera y verifica SHA-256 sin red:

```powershell
python scripts/package_manifest.py . work/manifest.json
python scripts/package_manifest.py . work/manifest.json --verify
```

El manifiesto cubre código, guía, fixtures, dependencias de voz y scripts de
diagnóstico/arranque; el modelo Vosk se valida por separado con `--check` porque
se prepara como asset local antes de desconectar la red. Un archivo esencial ausente falla antes de iniciar. Una modificación posterior
produce `MISMATCH`; no se ignora silenciosamente. El modelo Vosk se prepara
antes de desconectar la red y se verifica con `scripts/setup_voice_model.py --check`.

