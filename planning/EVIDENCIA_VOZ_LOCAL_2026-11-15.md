# Evidencia de voz local — 2026-11-15

Esta evidencia corresponde únicamente a una prueba técnica del canal local en
la laptop de desarrollo. No es una medición de reconocimiento en mina, EPP ni
una validación de operador.

## Entorno

- Windows 11 (`Windows-11-10.0.26200-SP0`).
- Python 3.12.10 en `.venv`.
- Modelo local `models/vosk-model-small-es-0.42`.
- Dispositivos de entrada detectados: índices 0, 1, 4, 5, 9, 12, 15, 16, 17,
  20; se observaron entradas Realtek y el asignador de sonido de Microsoft.
- No se guardó audio y no se usó red.

## Ensayo de captura

Comando ejecutado desde la raíz:

```powershell
@' ... VoiceRecognizer(...); time.sleep(2); recognizer.stop(...) ... '@ |
  .venv\Scripts\python.exe -
```

Resultado observado:

```text
started=True
is_listening_after_stop=False
events=[
  ('starting', 'Cargando reconocimiento de voz local.'),
  ('listening', 'Micrófono activo; reconocimiento sin Internet.'),
  ('stopped', 'Micrófono desactivado.')
]
```

No se pronunció una frase de comando durante este ensayo; por tanto, no se
declara exactitud, latencia de reconocimiento ni falsa aceptación. La prueba
de frases con voces humanas, ruido y EPP permanece pendiente y debe ejecutarse
con consentimiento, sin publicar WAV privados.

## Cobertura relacionada

- `tests/test_voice.py` y `tests/test_voice_pipeline.py`: hilo, errores,
  transcripción final, sesión, escucha y generación.
- `scripts/diagnose_offline.py --json`: `required_ok=true`.
- `planning/RESULTADOS_VALIDACION.md`: V-10 permanece parcial hasta completar
  el ensayo de pérdida de micrófono y el corpus autorizado.
