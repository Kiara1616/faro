# Smoke de exportación de auditoría redactada

Fecha: 2026-11-15  
Alcance: SQLite sintético de un solo registro; no contiene datos reales ni
audio.

## Resultado observado

Se creó una bitácora temporal con una decisión ficticia y se ejecutó la misma
función de exportación usada por `scripts/export_audit.py` con `redact=True`.
La salida verificada fue:

```json
{"record_count": 1, "audio_included": false, "redacted": true}
```

También se comprobó que `operator_label` y `transcript` quedaran como
`<operator-redacted>` y `<transcript-redacted>`. Los archivos temporales fueron
limpiados después de la prueba.

## Límites

Es un smoke de formato y redacción, no una auditoría de datos de ORICA ni una
prueba de retención legal. No se exportó audio ni una base de producción.
