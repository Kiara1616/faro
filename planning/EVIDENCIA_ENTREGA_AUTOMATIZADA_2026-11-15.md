# Evidencia automatizada de entrega

Fecha de ejecución: 2026-11-15  
Commit de código/documentación: `69c36ef`
Entorno: Windows 11 (`10.0.26200`) · Python 3.12.10

## Resultados

| Gate | Resultado observado |
|---|---|
| Suite aislada | `191 passed` no-UI + `3 passed` UI offscreen |
| Escenario normal | `simulation_only=true`, taladros 101 y 102, estado `cerrado`, 6 terminales `completed` |
| Escenario de fallo | `fallo_brazo`, estado `fallo`, 1 terminal `failed`, 0 taladros completados |
| Diagnóstico offline | `required_ok=true`; plan, modelo, PySide6, pytest, Vosk, sounddevice y micrófonos detectados |
| Manifiesto | regenerado para el contenido actual y `--verify` devuelve `OK` |
| CI Qt Windows | run `43768610935` verde tras corregir teardown de `QApplication` |

## Incidencia detectada durante la verificación

La primera ejecución de `package_manifest.py --verify` devolvió `MISMATCH`
porque el manifiesto local aún correspondía a la revisión anterior y faltaban
los documentos añadidos recientemente. Se regeneró el manifiesto y la segunda
verificación devolvió `OK`. Esto confirma que el gate detecta cambios de
entrega; no se ocultó ni se trató el desajuste como aprobación.

## Límites

Esta evidencia es automatizada y offline. No demuestra corpus humano,
ergonomía, ruido/EPP, desconexión física del micrófono, red físicamente
desactivada, comprensión por participantes ni aprobación industrial.
