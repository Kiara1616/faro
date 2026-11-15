# Informe de avance F-01 a F-20 — Faro

**Corte:** 2026-11-15  
**Repositorio:** `Kiara1616/faro`  
**Rama:** `main`  
**Último commit:** `f931f6e`
**Alcance:** simulador local académico; sin conexión a maquinaria, PLC, MMU,
LOADPlus, ProBlast, LoRa, radio industrial, sensores reales ni sistemas de
iniciación.

Este informe es trazabilidad de implementación. Una issue no se considera
cerrada por tener código: requiere pruebas, documentación, revisión
independiente y, cuando el criterio lo exige, evidencia manual registrada.

La ejecución de las validaciones humanas pendientes está preparada en
`planning/PLAN_VALIDACION_MANUAL.md`; sus campos sin resultado se mantienen
como pendientes y no se interpretan como aprobados.

La evidencia automatizada de la puerta de entrega (incluido un desajuste de
manifiesto detectado y corregido) está en
`planning/EVIDENCIA_ENTREGA_AUTOMATIZADA_2026-11-15.md`.

El inventario de responsables y criterios de cierre para las pruebas todavía
manuales está en `planning/REGISTRO_PENDIENTES_MANUALES.md`.

La preparación y transferencia offline del modelo Vosk están especificadas en
`planning/MODELO_VOSK_OFFLINE.md`; `models/` no se presenta como contenido
versionado de GitHub.

El inventario local de archivos esenciales y hashes está en
`planning/EVIDENCIA_MODELO_LOCAL_2026-11-15.md`.

El smoke de exportación redactada de SQLite está en
`planning/EVIDENCIA_EXPORT_AUDIT_2026-11-15.md`.

El límite estático de red del runtime está comprobado en
`planning/EVIDENCIA_LIMITE_OFFLINE_2026-11-15.md`; la red física sigue siendo
un gate manual.

## Estado por issue

| Issue | Estado | Commit / evidencia | Pruebas | CI | Revisión independiente | Pendientes | Cerrada |
|---|---|---|---|---|---|---|---|
| F-01 | Cerrada | alcance, decisiones y preguntas ORICA | documental | histórico | aprobada | ninguno técnico | Sí |
| F-02 | Implementada | `7cfad46`, contrato y comentarios GitHub | 194 local (191 no-UI + 3 UI) | CI pendiente guard offline | aprobada código | revisión manual voz/lógica/UI | No |
| F-03–F-09 | Cerradas | fixtures, dominio, simulador, excepciones, sesión, auditoría y parser | suite | CI | aprobadas | ninguno técnico | Sí |
| F-10 | Parcial | `55c887c`, evidencia de captura local | 194 local + 14 dirigidas voz | CI pendiente guard offline | aprobada código por voz/QA | frase hablada y ruido/EPP | No |
| F-11 | Pendiente externo | evaluador listo | tests evaluador | CI | pendiente | dos voces consentidas, ruido, p50/p95 | No |
| F-12 | Implementada | Qt + resumen de confirmación; contrato visual y smoke | Qt offscreen, 3 pruebas UI | CI pendiente guard offline | `/root/ui_contract_reviewer` aprobó código | captura y tres fixtures | No |
| F-13 | Implementada | estados textuales y alertas; contrato visual | Qt/integración, 3 pruebas UI | CI pendiente guard offline | `/root/ui_contract_reviewer` aprobó código | ensayo visual manual | No |
| F-14 | Parcial | mensajes y fallback teclado | Qt offscreen | CI | pendiente | dos usuarios, ergonomía y TTS | No |
| F-15 | Parcial | integración voz-parser-dominio-simulador-UI + escenarios offline | 194 local; V-12/V-13 | CI pendiente guard offline | pendiente manual | recorrido voz de dos taladros | No |
| F-16 | Parcial | diagnóstico, manifiesto, límite offline y guía; `required_ok=true` | 194 + diagnóstico + manifest | CI pendiente guard offline | pendiente manual | copia limpia sin red y reinicio | No |
| F-17 | Parcial | `RESULTADOS_VALIDACION.md` actualizado; V-12/V-13 | 194 local | CI pendiente guard offline | `/root/demo_reviewer` aprobó escenarios | corpus y V-10 | No |
| F-18 | Pendiente externo | protocolo preparado | no ejecutada | — | pendiente | dos participantes no autores | No |
| F-19 | Parcial | pitch, FAQ y fallback | documental | CI | pendiente | ensayo cronometrado y acta | No |
| F-20 | Pendiente | manifiesto fail-closed, límite offline y checklist | 194 local + manifest OK; V-12/V-13 | CI pendiente guard offline | pendiente | paquete limpio, tag y cotejo cruzado | No |

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
.venv\Scripts\python.exe scripts\verify_demo_scenarios.py --json
```

## Preguntas pendientes para ORICA

Equipo objetivo, órdenes permitidas/prohibidas, señales de estado, autoridad
de confirmación, interbloqueos, política de audio/transcripciones, requisitos
offline, EPP/ruido representativo, criterios de piloto y proceso de seguridad
funcional. Hasta recibir respuestas, cualquier integración real es una ruta
futura y no una capacidad actual.
