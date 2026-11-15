# Informe de avance F-01 a F-20 — Faro

**Corte:** 2026-11-15  
**Repositorio:** `Kiara1616/faro`  
**Rama:** `main`  
**Último commit:** `96cdcc6`  
**Alcance:** simulador local académico; sin conexión a maquinaria, PLC, MMU,
LOADPlus, ProBlast, LoRa, radio industrial, sensores reales ni sistemas de
iniciación.

Este informe es trazabilidad de implementación. Una issue no se considera
cerrada por tener código: requiere pruebas, documentación, revisión
independiente y, cuando el criterio lo exige, evidencia manual registrada.

## Estado por issue

| Issue | Estado | Commit / evidencia | Pruebas | CI | Revisión independiente | Pendientes | Cerrada |
|---|---|---|---|---|---|---|---|
| F-01 | Cerrada | alcance, decisiones y preguntas ORICA | documental | histórico | aprobada | ninguno técnico | Sí |
| F-02 | Implementada | `7cfad46`, contrato y comentarios GitHub | 189 local | CI exitoso | aprobada código | revisión manual voz/lógica/UI | No |
| F-03–F-09 | Cerradas | fixtures, dominio, simulador, excepciones, sesión, auditoría y parser | suite | CI | aprobadas | ninguno técnico | Sí |
| F-10 | Parcial | `55c887c`, evidencia de captura local | 179 local + 14 dirigidas voz | run `43761928495` verde | aprobada código por voz/QA | frase hablada y ruido/EPP | No |
| F-11 | Pendiente externo | evaluador listo | tests evaluador | CI | pendiente | dos voces consentidas, ruido, p50/p95 | No |
| F-12 | Implementada | Qt + resumen de confirmación | Qt offscreen | run `43760720277` verde | pendiente manual | captura y tres fixtures | No |
| F-13 | Implementada | estados textuales y alertas | Qt/integración | CI | parcial | ensayo visual manual | No |
| F-14 | Parcial | mensajes y fallback teclado | Qt offscreen | CI | pendiente | dos usuarios, ergonomía y TTS | No |
| F-15 | Parcial | integración voz-parser-dominio-simulador-UI | 189 local | run `43763297246` verde | pendiente manual | recorrido voz de dos taladros | No |
| F-16 | Parcial | diagnóstico, manifiesto y guía | suite + diagnóstico | CI | pendiente | copia limpia sin red y reinicio | No |
| F-17 | Parcial | `RESULTADOS_VALIDACION.md` actualizado | matriz automatizada | CI | pendiente | corpus y V-10 | No |
| F-18 | Pendiente externo | protocolo preparado | no ejecutada | — | pendiente | dos participantes no autores | No |
| F-19 | Parcial | pitch, FAQ y fallback | documental | CI | pendiente | ensayo cronometrado y acta | No |
| F-20 | Pendiente | manifiesto fail-closed y checklist | 189 local + manifest OK | CI en ejecución | pendiente | paquete limpio, tag y cotejo cruzado | No |

## Arquitectura y flujo

```text
Vosk local + sounddevice (hilo)
        ↓ transcripción final
VoicePipeline / parser cerrado
        ↓ intención tipada + sesión + generación
FaroController (composición, confirmación, auditoría)
        ↓ reglas deterministas
FaroDomain (estados y alertas)
        ↓ solicitud autorizada
SimulatedMMU (eventos por command_id)
        ↓
PySide6 UI + SQLite local sin audio
```

La entrada escrita usa el mismo controlador como fallback. `CONFIRMACION_PENDIENTE`
es explícito; una acción crítica solo llega al simulador después de confirmar.
`pausar` durante confirmación cancela localmente; durante una acción autorizada
solicita cancelación simulada. Timeout y resultado desconocido requieren
revisión y nunca se interpretan como éxito.

## Tecnologías, seguridad y límites

Python 3.12, PySide6, Vosk, sounddevice, SQLite, JSON, pytest y Docker solo
para pruebas headless. No se usa LLM para decidir órdenes ni se añade Go sin
un contrato industrial de ORICA. La sesión es ficticia, no biométrica; no se
guardan WAV ni se envía audio a red; el simulador no reemplaza controles
físicos ni autoriza maquinaria.

## Verificación

```powershell
.venv\Scripts\python.exe -m pytest -q
python -m py_compile app.py
.venv\Scripts\python.exe scripts\diagnose_offline.py --json
.venv\Scripts\python.exe scripts\package_manifest.py . work\manifest.json
.venv\Scripts\python.exe scripts\package_manifest.py . work\manifest.json --verify
```

## Preguntas pendientes para ORICA

Equipo objetivo, órdenes permitidas/prohibidas, señales de estado, autoridad
de confirmación, interbloqueos, política de audio/transcripciones, requisitos
offline, EPP/ruido representativo, criterios de piloto y proceso de seguridad
funcional. Hasta recibir respuestas, cualquier integración real es una ruta
futura y no una capacidad actual.
