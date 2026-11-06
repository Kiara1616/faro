# Entrega Faro — guía de traspaso

Faro es un prototipo académico de consola local para una MMU **simulada**. No
controla maquinaria, PLC, radio ni sistemas de iniciación.

## Arranque

1. Instalar Python 3.12 y crear `.venv`.
2. Instalar `requirements.txt` (y `requirements-dev.txt` para pruebas).
3. Preparar/verificar el modelo Vosk antes de desconectar la red.
4. Ejecutar `scripts/diagnose_offline.py --json`.
5. Abrir `app.py`; `FARO_SCENARIO=normal` es el valor por defecto.

## Verificación

```powershell
python -m pytest -q
python scripts/package_manifest.py . work/manifest.json --verify
python scripts/diagnose_offline.py --json
```

Para ensayar un fallo: `FARO_SCENARIO=fallo_brazo python app.py`. La tarjeta de
operación muestra el escenario y todos los eventos quedan rotulados como
simulación. Si el micrófono falla, usar entrada escrita; no inventar audio.

## Contenido y límites

La entrega incluye código, fixtures ficticios, documentación, manifiesto y
resultados. No incluye WAV humanos, SQLite de ensayo, logs, secretos ni material
privado del briefing. Las preguntas a ORICA siguen pendientes hasta recibir
respuesta autorizada. No se afirma autenticación biométrica, desempeño minero,
ahorro, cumplimiento normativo ni compatibilidad industrial.

## Traspaso

La persona receptora debe ejecutar la guía sin ayuda oral, registrar versión de
Windows/Python, resultado normal y fallo, y anotar cualquier paso que requiera
aclaración. El cierre formal requiere esa acta; el documento no simula haberla
realizado.

