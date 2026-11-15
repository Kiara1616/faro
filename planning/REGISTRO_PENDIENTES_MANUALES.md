# Registro de pendientes manuales y externos

Fecha de corte: 2026-11-15  
Commit de referencia: `e2707d5`

Este registro evita confundir código preparado con evidencia ejecutada. Los
pendientes no son defectos del simulador por sí mismos: requieren personas,
hardware, red controlada o una revisión externa. Ningún campo `Pendiente` puede
usarse como resultado positivo.

| Issue | Evidencia faltante | Responsable de ejecutarla | Registro requerido | Criterio para cerrar |
|---|---|---|---|---|
| F-02 | Comparación manual de contrato, parser, motor y UI | Producto + voz + segunda persona | Checklist de órdenes y rechazos | Todas las intenciones y negativos cotejados |
| F-10 | Frase hablada, ruido/EPP y desconexión física | Voz/QA en la laptop | Acta sin WAV privado, dispositivo y latencias | Ciclo limpio observado y fallos registrados |
| F-11 | Dos voces autorizadas y corpus por condición | QA + dos voluntarios consentidos | CSV anonimizado + JSON de métricas | Denominadores, falsas aceptaciones, p50/p95 |
| F-12 | Captura y recorrido de tres fixtures | Producto/UI | Capturas anonimizadas y checklist | Taladro, plan, estado y simulación legibles |
| F-13 | Revisión visual de todos los estados | QA/UI | Matriz estado→texto→bitácora | Ningún estado ambiguo o solo por color |
| F-14 | Dos usuarios, auricular, contraste y TTS opcional | Producto/UI | Hoja de comprensión y decisión TTS | Usuarios explican aceptado/completado/rechazo |
| F-15 | Recorrido humano de dos taladros, voz y teclado | Integración + QA | Acta y cotejo SQLite/UI/estado | Un comando, una solicitud, estados coincidentes |
| F-16 | Red desactivada, copia limpia y reinicio | DevOps + segunda persona | Diagnóstico, versiones y salida del ensayo | Arranca y repite el flujo sin red |
| F-17 | Corpus/V-10 y revisión cruzada | QA + seguridad | Matriz actualizada y firma | Cero P0 abiertos que avancen tras rechazo |
| F-18 | Dos participantes no autores | Producto/UI | Tiempos, errores, cambios y repetición | Confusión corregida y repetida |
| F-19 | Ensayo cronometrado y captura/video | Producto + presentador | Acta de cinco minutos y backup | Guion completo sin afirmaciones no evidenciadas |
| F-20 | Cotejo final, exclusiones, reinicio y tag | Revisor cruzado | Manifest, hash, checklist y aprobación | Todos los gates aprobados; recién entonces tag |

## Evidencia ya disponible

- 191 pruebas automatizadas aprobadas (190 no-UI + 1 UI offscreen aislada).
- Escenarios offline normal y fallo inyectado.
- Diagnóstico offline `required_ok=true` en Windows 11/Python 3.12.10.
- Smoke UI Qt offscreen `Qt smoke UI OK`.
- Manifiesto regenerado y verificado `OK`.
- No hay corpus WAV humano en el repositorio; no se declara precisión de voz.
- No hay conexión industrial ni audio privado en la entrega.

## Procedimiento

La ejecución debe seguir `planning/PLAN_VALIDACION_MANUAL.md`. Cada resultado
se añade al informe F-01–F-20 y al comentario de la issue correspondiente. Si
un ensayo no puede ejecutarse, se conserva como `Pendiente` y se registra el
motivo; nunca se reemplaza por una inferencia.
