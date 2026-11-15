# Plan de validación manual para Faro

La hoja operativa resumida para ejecutar este plan está en
`planning/HOJA_EJECUCION_MANUAL.md`.

Versión de trabajo: `ad18fc0` · fecha: 2026-11-15

Este plan convierte los criterios humanos pendientes de F-10, F-11, F-12,
F-13, F-14, F-16, F-18, F-19 y F-20 en una sesión ejecutable. Evalúa el
prototipo ficticio y la claridad de la demo; no certifica una operación minera,
un MMU real ni un control de seguridad funcional.

## Reglas de evidencia

- Usar una copia identificada por commit. No modificar el repositorio durante
  la sesión salvo que el cambio quede registrado como defecto.
- No grabar ni publicar nombres completos, voces, rostros, pantallas con datos
  personales ni audio sin consentimiento explícito.
- No conectar Faro a maquinaria, PLC, radio, LoRa, LOADPlus, ProBlast,
  sensores ni redes industriales.
- Registrar resultados observados, incluidos fallos. Un campo vacío significa
  «no ejecutado», no «aprobado».
- Un observador toma tiempos y no explica el significado de los estados hasta
  que la tarea haya terminado.

## Roles para la sesión

| Rol | Persona | Responsabilidad |
|---|---|---|
| Operador de prueba | P-01 / P-02 | Ejecutar tareas sin haber implementado la UI |
| Observador | — | Cronometrar, registrar errores y no dar pistas |
| Responsable técnico | — | Recuperar la aplicación, no alterar el resultado |
| Revisor cruzado | — | Cotejar commit, manifiesto y acta antes de cerrar F-20 |

## Preparación reproducible

1. Copiar el repositorio a una carpeta limpia y registrar `git rev-parse
   HEAD`, `git status --short`, versión de Windows y Python.
2. Preparar el modelo Vosk, fixtures y dependencias antes de cualquier prueba
   sin red.
3. Ejecutar y guardar las salidas:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q
   .\.venv\Scripts\python.exe scripts\diagnose_offline.py --json > work\diagnostico-offline.json
   .\.venv\Scripts\python.exe scripts\package_manifest.py . work\manifest.json
   .\.venv\Scripts\python.exe scripts\package_manifest.py . work\manifest.json --verify
   ```

4. Abrir la consola con `$env:FARO_SCENARIO="normal"` seguido de
   `.\.venv\Scripts\python.exe app.py`. Si no se dispone de
   micrófono, registrar la limitación y ejecutar el mismo guion con teclado;
   no declarar una prueba de ASR.
5. Antes de desactivar la red, comprobar que el diagnóstico y el modelo ya
   están disponibles. La desconexión debe realizarla el responsable técnico
   según las reglas del equipo, sin cambiar configuraciones industriales.

## A. Voz local y fallos de captura — F-10

Registrar dispositivo seleccionado, hora, entorno acústico y si se usó
auricular. Pronunciar una sola frase autorizada por vez y conservar únicamente
la transcripción y decisión, no el WAV.

| Caso | Frase | Esperado | Observado |
|---|---|---|---|
| A1 | `Oye Faro, consultar estado` | Transcripción final, una decisión, sin duplicar | — |
| A2 | Frase fuera del vocabulario | Rechazo, sin solicitud al simulador | — |
| A3 | Repetir el mismo resultado final | Una sola acción | — |
| A4 | Detener captura durante escucha | Estado detenido/error visible, sin acción tardía | — |
| A5 | Micrófono desconectado antes de iniciar | Mensaje útil y fallback escrito | — |

Registrar latencia desde el fin de la frase hasta la decisión. A1–A4 pueden
ser ejecutados por una persona; A5 requiere una desconexión física segura del
auricular. Ningún resultado de esta sección autoriza control industrial.

## B. Corpus de voz — F-11

Usar mínimo dos voces autorizadas, etiquetadas `V-01` y `V-02`, sin nombres.
Cada voz ejecuta las mismas frases en condiciones separadas:

1. limpio;
2. ruido reproducido controlado;
3. EPP/auricular, si está disponible;
4. sintético, marcado como tal y nunca mezclado con humano.

Para cada fila registrar `caso, voz, condición, frase_esperada,
transcripcion, aceptada, accion_esperada, falsa_aceptacion,
latencia_ms`. Calcular denominador, falsas aceptaciones, p50 y p95 por
condición. Si una condición no se ejecuta, escribir `no ejecutada` y mantener
la métrica ausente.

## C. UI y comprensión — F-12, F-13, F-14, F-18

Dos participantes que no hayan implementado `faro/ui.py` ejecutan sin pistas:

1. Seleccionar y consultar taladro 101.
2. Preparar carga con producto alfa, 100 kg.
3. Intentar extender brazo sin zona libre y explicar el rechazo.
4. Describir la diferencia entre escuchado, aceptado, en curso y completado.
5. Repetir con zona libre y esperar completado.
6. Intentar producto divergente y explicar la acción segura siguiente.

El observador debe recorrer también los tres fixtures (normal, divergente y
bloqueado) y marcar cada estado textual visible: `escuchado`, `interpretado`,
`validando`, `en curso`, `completado`, `rechazado`, `fallido`, `cancelado`,
`timeout`, `resultado desconocido` y `requiere revisión`. Confirmar que una
demora permanece en curso, que un evento ajeno no cambia la vista y que el
motivo se lee sin depender del color.

En la misma pasada registrar si el foco y el recorrido por teclado funcionan,
si el texto se lee a distancia de laptop, si el contraste es suficiente y si
un auricular permite oír la respuesta. Si se prueba TTS, anotar si se incluye
o se excluye del prototipo; la UI debe seguir mostrando el resultado si TTS
falla.

Registrar por tarea:

| Participante | Tarea | Inicio/fin | Tiempo s | Primer intento | Estado percibido | Estado real | Ayuda | Cambio |
|---|---|---|---:|---|---|---|---|---|
| P-01 | 1–6 | — | — | — | — | — | — | — |
| P-02 | 1–6 | — | — | — | — | — | — | — |

Puerta: si alguien confunde aceptado con completado, corregir el texto,
registrar el commit y repetir únicamente la tarea afectada. Adjuntar capturas
anonimizadas antes/después.

## D. Flujo integrado y dos taladros — F-15

Con teclado y luego con voz (si A1–A5 fue válida), ejecutar el escenario normal
de dos taladros y confirmar que UI, estado y SQLite muestran el mismo
`command_id`. Después repetir con `FARO_SCENARIO=fallo_brazo` y verificar que el
taladro no se marca como completado. Usar el resultado automatizado de
`scripts/verify_demo_scenarios.py --json` como evidencia de simulación, y
registrar por separado cualquier recorrido humano.

Durante el recorrido, lanzar una intención por teclado y otra por voz casi al
mismo tiempo (solo en el simulador) y comprobar que existe como máximo una
solicitud para la intención. Ejecutar además una pausa/cancelación, un timeout
o un fallo inyectado y registrar la recuperación exigida por la UI.

## E. Arranque sin Internet y congelamiento — F-16, F-19, F-20

Con la red desactivada por el responsable técnico:

1. Ejecutar diagnóstico y abrir Faro.
2. Completar un caso normal y un rechazo por producto/kg.
3. Cerrar y reiniciar la aplicación.
4. Repetir el caso normal por teclado si el micrófono no está disponible.
5. Generar y verificar el manifiesto.
6. Un segundo revisor coteja commit, archivos, modelo y hashes en otra carpeta.
7. Solo si todos los campos están aprobados, crear el tag `faro-demo-YYYYMMDD`.

Antes del tag, realizar un ensayo cronometrado de cinco minutos usando
`planning/PITCH_5_MINUTOS.md`: problema, propuesta, flujo normal, rechazo,
fallo, métricas, arquitectura y límites. Registrar duración, preguntas no
respondidas y si el fallback por teclado se pudo ejecutar. El ensayo no debe
afirmar ahorro, reducción de accidentes, aprobación de ORICA ni desempeño
minero.

| Gate | Resultado | Evidencia | Revisor |
|---|---|---|---|
| Copia limpia | Pendiente | ruta/commit | — |
| Red desactivada | Pendiente | acta y hora | — |
| Reinicio | Pendiente | salida observada | — |
| Caso normal | Pendiente | JSON/captura | — |
| Caso de fallo | Pendiente | JSON/captura | — |
| Manifiesto cotejado | Pendiente | SHA-256 | — |
| Exclusiones revisadas | Pendiente | sin WAV/SQLite/logs/secretos/privado | — |
| Pitch de 5 minutos | Pendiente | acta/cronómetro | — |
| Segundo revisor | Pendiente | firma o comentario | — |

## Plantilla de acta

```text
Fecha/hora:
Commit:
Windows/Python:
Participantes anonimizados:
Dispositivo/condición de voz:
Pruebas ejecutadas:
Resultados observados:
Defectos encontrados:
Correcciones y nuevos commits:
Pruebas repetidas:
Evidencia adjunta (sin audio privado):
Revisor cruzado:
Decisión por issue (F-10..F-20):
```

La acta debe enlazarse desde `RESULTADOS_VALIDACION.md` y desde los comentarios
de GitHub. Hasta completar los campos pendientes, las issues correspondientes
permanecen abiertas y no se crea el tag final.
