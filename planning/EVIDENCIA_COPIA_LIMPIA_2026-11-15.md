# Evidencia de copia limpia — 2026-11-15

Repositorio: `Kiara1616/faro`  
Commit reconstruido: `f5e209b`  
Script: `scripts/verify_clean_copy.ps1`  
Entorno: Windows 11 · Python 3.12.10 · modelo Vosk local disponible.

## Resultado observado

| Gate | Resultado |
|---|---|
| Diagnóstico offline | `required_ok=true` |
| Suite completa | `195 passed` |
| Escenario normal | estado `cerrado`, taladros 101 y 102, seis terminales `completed` |
| Escenario `fallo_brazo` | estado `fallo`, cero taladros completados, un terminal `failed` |
| Manifiesto | generado y `--verify` = `OK` |
| Limpieza | carpeta temporal eliminada por `finally` |

## Qué demuestra

El código versionado, los fixtures, el modelo local y los scripts pueden
reconstruirse en una carpeta temporal y ejecutar los gates automatizables sin
depender de la ruta de trabajo original.

## Qué no demuestra

Esta prueba no deshabilitó físicamente la red, no sustituye un reinicio
observado por el equipo, no mide voces humanas/ruido/EPP y no es validación de
maquinaria ni de operación minera. Es evidencia automatizada de empaquetado y
arranque offline preparado.
