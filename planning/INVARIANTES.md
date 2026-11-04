# Invariantes de seguridad de Faro v1

Estas reglas protegen únicamente el simulador ficticio. No implementan un paro
de emergencia, un interlock certificado, control de acceso biométrico ni una
garantía para maquinaria real. Cualquier integración futura debe reemplazar
los supuestos por requisitos y pruebas de ORICA.

| ID | Invariante comprobable | Prueba | Resultado |
|---|---|---|---|
| I-01 | Una orden rechazada conserva exactamente el estado operacional anterior. | `test_rejected_commands_do_not_mutate_operational_state` | Cumple |
| I-02 | Existe como máximo una acción pendiente; una orden paralela o un cambio de taladro se rechaza. | `test_pending_action_rejects_duplicate_change_and_unrelated_event` | Cumple |
| I-03 | Taladro, producto y kg deben coincidir con la malla ficticia antes de cargar. | `test_wrong_values_and_methods_cannot_start_action` | Cumple |
| I-04 | Movimiento requiere método correcto y señal ficticia `zone_clear=True`; el valor por defecto es fail-closed. | `test_wrong_values_and_methods_cannot_start_action` | Cumple |
| I-05 | Un estado operativo de éxito solo aparece después de un evento final correlacionado por `command_id`. | `test_acceptance_progress_and_completion_are_distinct` | Cumple |
| I-06 | Evento duplicado, tardío o con ID ajeno no completa ninguna acción. | `test_duplicate_wrong_id_and_busy_requests_do_not_complete` | Cumple |
| I-07 | Fallo o cancelación no permiten iniciar carga ni cerrar el taladro. | `test_failed_or_cancelled_action_never_completes` | Cumple |
| I-08 | Una finalización que compite con una pausa queda en `RESULTADO_DESCONOCIDO`, nunca en éxito automático. | `test_completion_racing_with_pause_requires_reconciliation` | Cumple |
| I-09 | Voz exige sesión activa, modo voz, escucha explícita y generación vigente; manual y voz no actúan simultáneamente. | `test_voice_mode_requires_explicit_listening_and_current_generation` | Cumple |
| I-10 | Rechazo del simulador se reconcilia en el mismo ID y no deja una acción falsamente completada. | `test_rejected_submission_reconciles_domain_without_false_completion` | Cumple |
| I-11 | Timeout configurable del simulador pasa a `RESULTADO_DESCONOCIDO`; no se reenvía ni se infiere éxito. | `test_timeout_is_conservative_and_does_not_complete`, `test_controller_timeout_is_audited_and_never_replayed` | Cumple |

## Pausa simulada frente a emergencia física

`pausar` solo solicita una cancelación al simulador y espera un evento. No es un
paro físico de emergencia, no desenergiza equipos y no sustituye controles
manuales. La interfaz y el pitch deben decirlo explícitamente. La parada física,
interlocks, autoridad de mando, radio y procedimiento de emergencia quedan
pendientes de definición y aprobación de ORICA.

## Límites del alcance

- No hay sockets, PLC, radio, salidas físicas ni órdenes a una MMU real.
- La etiqueta de operador de la sesión es ficticia; no es autenticación.
- La zona despejada es una señal simulada introducida por la prueba, no un
  sensor real.
- El simulador no demuestra SIL/PL, cumplimiento normativo ni desempeño en
  ruido minero/EPP.

## Revisión

La tabla se rastrea a pruebas automatizadas y a la matriz de validación de
[`RESULTADOS_VALIDACION.md`](RESULTADOS_VALIDACION.md). Antes de cerrar el issue,
producto y seguridad deben revisar que los mensajes visibles mantengan la
distinción entre aceptación, ejecución, finalización, pausa simulada y paro
físico.

