# Resultados de validación de Faro

Fecha de corte: 2026-11-15 · versión: `d636c29` · entorno local: Windows 11,
Python 3.12.10. Esta matriz valida únicamente el simulador ficticio; no es una
certificación de seguridad ni una validación de maquinaria ORICA.

## Puerta automática

| Métrica | Resultado | Denominador / evidencia |
|---|---:|---|
| Pruebas automatizadas exitosas | 191/191 | 190 no-UI + 1 UI offscreen, ejecutados aislados por estabilidad nativa Qt |
| CI Windows exitoso | 1/1 | run `43767273792`, tests + importación UI |
| CI Windows del commit actual | 1/1 | run `43767273792`, tests + importación UI |
| CI Windows del commit documental más reciente | 1/1 | run `43767273792`, tests + importación UI |
| Órdenes rechazadas que llegan al simulador | 0 | `test_rejected_order_never_reaches_simulator_or_marks_success` |
| Eventos con ID ajeno que completan una acción | 0 | `test_duplicate_wrong_id_and_busy_requests_do_not_complete` |
| Fallos/cancelaciones que permiten cierre | 0 | `test_failed_or_cancelled_action_never_completes` |
| Discrepancias de plan que inician carga | 0 | `test_wrong_values_and_methods_cannot_start_action`, simulador |
| Diagnóstico offline preparado | `required_ok=true` | Python 3.12.10, PySide6, Vosk, sounddevice, modelo y micrófonos detectados |
| Smoke UI headless | `Qt smoke UI OK` | `planning/EVIDENCIA_UI_OFFSCREEN_2026-11-15.md`; no evidencia humana |
| Puerta automatizada de entrega | `OK` tras regenerar manifiesto | `planning/EVIDENCIA_ENTREGA_AUTOMATIZADA_2026-11-15.md` |

## Casos reproducibles

| ID | Caso | Esperado | Observado | Severidad | Evidencia / resolución |
|---|---|---|---|---|---|
| V-01 | Taladro inexistente o bloqueado | Rechazo, sin mutar estado | Cumple | P0 | `test_id_and_blocked_hole_alerts_are_transient_and_correctable` |
| V-02 | ID de taladro distinto al seleccionado | Rechazo y alerta | Cumple | P0 | `test_rejected_commands_do_not_mutate_operational_state` |
| V-03 | Producto o kg divergentes | No preparar/iniciar carga | Cumple | P0 | `test_wrong_values_and_methods_cannot_start_action` |
| V-04 | Zona ocupada / adaptador ocupado | Rechazo reconciliado a `fallo` | Cumple | P0 | `test_rejected_submission_reconciles_domain_without_false_completion` |
| V-05 | Orden repetida o evento duplicado | No duplicar acción | Cumple | P0 | `test_duplicate_wrong_id_and_busy_requests_do_not_complete` |
| V-06 | Pausa/cancelación y resultado tardío | `resultado_desconocido`, nunca completar automáticamente | Cumple | P0 | `test_completion_racing_with_pause_requires_reconciliation` |
| V-07 | Fallo de brazo/manguera | `fallo`, no cerrar taladro | Cumple | P0 | `test_injected_failure_and_cancellation`, `test_failed_or_cancelled_action_never_completes` |
| V-08 | Modo manual con frase de voz | Rechazo por voz deshabilitada | Cumple | P0 | `test_session_requires_explicit_start_and_rejects_voice_in_manual` |
| V-09 | ASR desconocido, negación o ambigüedad | No crear comando ni solicitud | Cumple | P0/P1 | `tests/test_parser.py`, `tests/test_voice_pipeline.py` |
| V-10 | Pérdida de micrófono/modelo | Mensaje de error; texto sigue disponible | Parcial | Manual en laptop | `faro/voice.py`, `scripts/diagnose_offline.py` |
| V-11 | Reinicio y auditoría | Conservar decisiones/eventos, no audio | Cumple | P1 | `tests/test_audit.py`, `tests/test_controller.py` |
| V-12 | Escenario normal de dos taladros | Cerrar 101 y 102 con eventos terminales completados | Cumple | P0/P1 | `scripts/verify_demo_scenarios.py --json`, sin red/hardware |
| V-13 | Fallo de brazo inyectado | Entrar en `fallo`, no marcar taladro como completado | Cumple | P0 | `scripts/verify_demo_scenarios.py --json`, sin red/hardware |

## Métricas de voz

No se declara una tasa de reconocimiento minero sin corpus humano autorizado.
El evaluador (`scripts/evaluate_voice.py`) exige denominadores separados por
condición (limpio, ruido, EPP/sintético), reporta falsas aceptaciones y p50/p95.
El corpus humano, la medición con EPP y la prueba de micrófono real quedan como
acciones manuales antes del pitch; sus resultados deben añadirse aquí sin
mezclarlos con audio sintético.

## Revisión de cierre

- [x] Ninguna orden rechazada cambia el estado operativo ni llega al simulador.
- [x] Eventos se correlacionan por `command_id`; eventos tardíos/ajenos no completan.
- [x] El modo voz exige sesión, escucha explícita y generación vigente.
- [x] Auditoría local no almacena audio.
- [ ] Ejecutar V-10 y el corpus humano autorizado en la laptop de demostración.
- [ ] Revisión cruzada por una segunda persona y adjuntar JSON del diagnóstico offline.
- [x] Confirmación crítica, expiración, cancelación, contexto y generación de voz obsoleta probados en controlador.
- [x] Escenarios deterministas normal/fallo reproducibles offline y separados de evidencia humana.

