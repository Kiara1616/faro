# Hoja de ejecución manual — Faro

Usar esta hoja con una copia preparada del repositorio. No registrar nombres
completos ni audio privado en GitHub. Las pruebas son del simulador y no son
validación minera.

## Roles

| Rol | Persona | Firma/fecha |
|---|---|---|
| Operador de prueba | __________________ | __________________ |
| Observador/cronometrista | __________________ | __________________ |
| Revisor cruzado | __________________ | __________________ |

## Preparación

- [ ] Confirmar commit probado: `git rev-parse HEAD` → ________________
- [ ] Ejecutar `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_offline_validation.ps1`.
- [ ] Registrar Windows/Python y resultado de `scripts/diagnose_offline.py --json`.
- [ ] Conectar auricular/micrófono autorizado; no guardar WAV.
- [ ] Tener a mano `planning/PLAN_VALIDACION_MANUAL.md` y esta hoja.

## Voz, F-02/F-10/F-11

1. Activar escucha con botón o F8; decir una orden permitida completa.
2. Repetir con una segunda voz autorizada.
3. Repetir con ruido reproducido y EPP disponible, sin publicar audio.
4. Decir una frase desconocida, una negación, un ID equivocado y un kg sin unidad.
5. Desconectar el micrófono durante escucha y comprobar mensaje, detención y
   fallback escrito.

Registrar: frase esperada, texto observado, aceptada/rechazada, latencia
aproximada, condición, falsa aceptación y evidencia visual. Para F-11 calcular
denominadores, p50 y p95 por condición; no reportar una métrica si faltan casos.

## UI y comprensión, F-12/F-13/F-14/F-18

- [ ] Pedir a dos personas que no implementaron la UI que ejecuten el guion sin
  explicarles los estados.
- [ ] Preguntar qué taladro, producto, kg, modo y resultado observan.
- [ ] Provocar un rechazo, una demora y un fallo; preguntar si distinguen cada
  estado de «completado».
- [ ] Registrar tiempo, errores, ayuda recibida y cambio aplicado.
- [ ] Repetir el paso confuso después del cambio y adjuntar captura anonimizada.

## Integración y entrega, F-15/F-16/F-17/F-19/F-20

1. Ejecutar el caso normal con dos taladros y guardar JSON/captura.
2. Ejecutar `$env:FARO_SCENARIO="fallo_brazo"; .venv\Scripts\python.exe scripts\verify_demo_scenarios.py --json` y guardar JSON/captura.
3. Deshabilitar físicamente la red, reiniciar Faro y repetir entrada escrita;
   registrar hora y resultado.
4. Cotejar `work/manifest.json` con la carpeta entregada y anotar SHA-256.
5. Ensayar el pitch con cronómetro; registrar duración, preguntas y revisor.
6. Solo si todo está aprobado, crear `faro-demo-YYYYMMDD` y anotar el tag.

## Resultado

| Gate | Resultado | Evidencia/ruta | Responsable |
|---|---|---|---|
| Voz limpia y dos voces | Pendiente | __________________ | __________________ |
| Ruido/EPP y micrófono | Pendiente | __________________ | __________________ |
| Comprensión de dos usuarios | Pendiente | __________________ | __________________ |
| Dos taladros normal/fallo | Pendiente | __________________ | __________________ |
| Red deshabilitada + reinicio | Pendiente | __________________ | __________________ |
| Manifiesto cotejado | Pendiente | __________________ | __________________ |
| Pitch ≤ 5 min | Pendiente | __________________ | __________________ |
| Revisión cruzada | Pendiente | __________________ | __________________ |

Una issue solo puede cerrarse cuando su evidencia esté completa, revisada y
comentada en GitHub. Si un gate no se ejecuta, conservar «Pendiente».
