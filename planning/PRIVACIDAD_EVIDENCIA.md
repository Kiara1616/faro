# Privacidad y exportación de evidencia

- Faro no guarda audio crudo; la bitácora SQLite contiene transcripción,
  decisión, estado y evento del simulador.
- Para presentar resultados se usa `scripts/export_audit.py`, que genera JSON
  con `simulation_only=true` y `audio_included=false`.
- Las voces humanas del corpus deben contar con consentimiento; los WAV no se
  suben al repositorio ni a la carpeta de entrega.
- SQLite de ensayo, WAV, logs y datos personales están excluidos por `.gitignore`.
- La limpieza de un ensayo consiste en retirar su SQLite y archivos de audio
  fuera del repositorio; el reporte exportado se conserva solo si está anonimizado.

Ejemplo:

```powershell
python scripts/export_audit.py data/faro-audit.sqlite3 work/auditoria-ficticia.json
```

