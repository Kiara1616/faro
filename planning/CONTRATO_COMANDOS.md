# Faro v1 — contrato de comandos del simulador

**Fecha:** 3 de noviembre de 2026 · **Issue:** F-02 · **Estado:** contrato interno propuesto. Se deriva del [alcance](ALCANCE_Y_DECISIONES.md) y del [briefing analizado](../Analisis_briefing_Faro_ORICA_2026-10-28.md). Las frases y confirmaciones son elecciones de Faro para pruebas, no instrucciones operativas aprobadas por ORICA.

## Frontera de entrada

La entrada es `{source: voice|text, transcript, session_id, timestamp}`. `voice` se procesa solo con escucha y modo voz activos; `text` es el control manual simulado o una herramienta de prueba. Ambos producen la misma intención tipada o `unknown/ambiguous`; ninguno llama directamente al adaptador. La sesión y el estado se verifican de nuevo **al confirmar** una acción.

F-07 añade una frontera obligatoria antes del motor: `Session(session_id, operator_label, mode, listening, generation)`. La etiqueta de operador es ficticia y no es autenticación biométrica. `voice` exige `mode=VOZ`, `listening=true` y la misma `generation` de captura; una respuesta de un hilo antiguo se rechaza. `text` es una entrada manual de prueba explícita y no enciende el micrófono. Cambiar a `MANUAL` o `DESHABILITADO` apaga la escucha y aumenta la generación; cambiar de modo mientras existe una acción pendiente se rechaza.

La puerta de voz de `app.py` exige «Oye Faro» al inicio de cada orden hablada. El operador puede decirlo junto con la orden o decirlo solo y dar una orden dentro de seis segundos. Las transcripciones sin prefijo se descartan antes del parser y no se guardan en la bitácora. La frase no activa la captura desde reposo: el micrófono se controla con botón/F8 y Vosk procesa audio localmente mientras está activo. Después de quitar el prefijo, el parser normaliza mayúsculas, espacios y acentos; solo admite variantes enumeradas, no usa similitud, LLM ni valores inferidos. Una frase con dos intenciones, negación o palabras adicionales de acción se rechaza completa.

## Datos y estados comunes

`hole_id` es un ID del fixture local, pronunciado o escrito completo. `product` coincide con uno de los nombres de la malla ficticia. `kg` es entero positivo con unidad explícita «kilos»/«kilogramos»; no se aceptan decimales en v1. Esta restricción es de parser de prototipo, pendiente de vocabulario real. Para comparar se exige igualdad exacta con el fixture; no se inventa tolerancia de campo.

Estados de tarea: `SIN_SELECCION`, `SELECCIONADO`, `CONSULTADO`, `PREPARADO`, `CONFIRMACION_PENDIENTE`, `MOVIMIENTO_EN_CURSO`, `POSICIONADO`, `CARGA_EN_CURSO`, `CARGADO`, `RETRACCION_EN_CURSO`, `RETRAIDO`, `CERRADO`, `FALLO`, `RESULTADO_DESCONOCIDO`. Una discrepancia o bloqueo rechazado se registra como **alerta pendiente separada** y no cambia el estado operativo. Los eventos de F-05 determinarán cuándo termina una acción. El modo de sesión es independiente: `VOZ`, `MANUAL`, `DESHABILITADO`.

## Matriz de intenciones

| Intención / frase canónica | Argumentos | Estados previos y condición | Efecto tras validación o evento | Confirmación | Rechazo específico |
| --- | --- | --- | --- | --- | --- |
| `consultar_estado` / «consultar estado» | Ninguno | Sesión activa, cualquier estado | Solo lectura del taladro, modo, acción y último resultado. | No | Sin sesión → «Inicie sesión ficticia». |
| `seleccionar_taladro` / «seleccionar taladro 101» | `hole_id` | `SIN_SELECCION`; ID existente, no bloqueado ni cerrado; si se pidió siguiente, debe ser el ID anunciado | Marca `SELECCIONADO`; aún no habilita movimiento/carga. | No | ID desconocido, bloqueado, cerrado, distinto del siguiente anunciado o ciclo anterior sin cerrar. |
| `consultar_taladro` / «consultar taladro 101» | `hole_id` | Debe ser el seleccionado; sin acción pendiente | Muestra plan y marca `CONSULTADO`. | No | ID distinto → mostrar actual y pedir selección explícita. |
| `consultar_plan` / «consultar plan» | Ninguno | Taladro seleccionado | Solo lectura de producto, kg y método previstos. | No | Sin taladro → pedir selección. |
| `preparar_carga` / «preparar carga» | Ninguno | `CONSULTADO`, plan íntegro, taladro no bloqueado | Marca `PREPARADO`; no mueve ni carga. | No | Plan ausente/bloqueado → alerta pendiente; estado operativo intacto. |
| `declarar_plan` / «validar producto alfa, 100 kilos» | `product`, `kg` | `PREPARADO`; taladro activo | Compara ambos con el plan; igualdad marca datos validados y resuelve alerta previa de discrepancia; divergencia crea alerta sin avanzar. | No | Producto, kg o unidad ausente/diferente → no cargar. |
| `extender_brazo` / «extender brazo» | Ninguno | `PREPARADO`, método brazo, datos validados, zona ficticia despejada | Solicitud al simulador; `POSICIONADO` solo tras `completed`. | Sí | Método distinto, zona ocupada, acción pendiente o estado incorrecto. |
| `extender_manguera` / «extender manguera» | Ninguno | Igual, con método manguera | Igual. | Sí | Igual. |
| `iniciar_carga` / «iniciar carga» | Ninguno | `POSICIONADO`, plan validado, sin alerta pendiente ni acción activa | Solicitud de carga simulada; `CARGADO` solo tras `completed`. | Sí | Datos divergentes o movimiento incompleto → no solicitar. |
| `pausar` / «pausar» | Ninguno | Movimiento/carga/retracción en curso | Pide cancelación simulada; estado queda en revisión hasta evento de cancelación. Si hay `CONFIRMACION_PENDIENTE`, cancela esa confirmación local sin enviar cancelación al simulador. | No | Sin acción activa → informar sin cambiar estado. |
| `retraer_brazo` / «retraer brazo» | Ninguno | `CARGADO`, método brazo, sin acción activa | Solicitud; `RETRAIDO` tras `completed`. | Sí | Método/estado incorrecto. |
| `retraer_manguera` / «retraer manguera» | Ninguno | `CARGADO`, método manguera, sin acción activa | Igual. | Sí | Igual. |
| `cerrar_taladro` / «cerrar taladro» | Ninguno | `RETRAIDO`, sin alerta pendiente ni acción activa | Marca `CERRADO`; audita cierre. | No | Retracción pendiente o fallo → no cerrar. |
| `siguiente_taladro` / «siguiente taladro» | Ninguno | `CERRADO` y existe un siguiente ID no bloqueado del fixture | Anuncia el siguiente ID operable y deja estado `SIN_SELECCION` para seleccionarlo explícitamente; informa los IDs bloqueados que omitió y conserva historial. | No | Taladro actual no cerrado o no quedan taladros operables; conservar `CERRADO`. |
| `cancelar_confirmacion` / «cancelar» | Ninguno | `CONFIRMACION_PENDIENTE` | Descarta la solicitud sin tocar estado operacional. | No | Sin confirmación → solo informa. |
| `confirmar` / «confirmar» | Ninguno | Confirmación vigente, mismos ID/plan/modo/sesión, ninguna otra acción | Envía exactamente una solicitud correlacionada al adaptador. | No | Vencida o contexto cambiado → descartar y repetir orden original. |
| `modo_manual` / «cambiar a modo manual» | Ninguno | Sin acción activa o tras recuperación explícita | Apaga escucha antes de habilitar entrada manual simulada. | No | Acción pendiente → bloquear transferencia y mostrar estado. |
| `modo_voz` / «cambiar a modo voz» | Ninguno | Sin acción activa, micrófono/modelo disponibles | Cambia modo; escucha sigue apagada hasta botón/F8. | No | Voz no disponible → mantener manual/deshabilitado. |

Los IDs, «producto alfa» y «100 kilos» de ejemplo son ficticios. F-03 fijará los valores exactos del fixture; F-09 generará gramática concreta de esos valores sin ampliar el alcance de esta matriz.

## Reglas generales de rechazo y mensajes

1. `unknown/ambiguous`, sesión inválida, modo incorrecto, taladro distinto, valor faltante, estado prohibido, alerta pendiente o acción en curso producen `accepted=false`, código de motivo y **cero solicitudes** al adaptador. Con una alerta de discrepancia se permiten consultas de solo lectura y una nueva declaración completa del plan ficticio para corregir el dato; las acciones de movimiento o carga siguen bloqueadas.
2. Un rechazo no modifica estado operacional. Se permite guardar el intento y mostrar una alerta separada con causa, plan y valor recibido. ID desconocido, dato faltante, método incorrecto o taladro bloqueado generan alerta transitoria: una entrada válida puede corregirlos sin atascar la sesión. Producto o kg divergentes generan alerta bloqueante del taladro; solo una declaración completa que coincida exactamente con el plan ficticio la resuelve. Si un dato coincide parcialmente, no se completa el argumento con el plan.
3. Cada decisión expone `command_id`, intención, argumentos, `state_before`, `state_after`, motivo y mensaje. Una solicitud aceptada puede pasar a `in_progress`; «completado» requiere evento final con el mismo ID.
4. La confirmación vence tras un plazo configurable, propuesto inicialmente de 10 segundos para pruebas. Al vencer, se elimina la solicitud pendiente; confirmar tarde no reenvía.
5. Un timeout del adaptador lleva a `RESULTADO_DESCONOCIDO`. Bloquea órdenes dependientes hasta revisión manual simulada; no se interpreta como éxito ni se reintenta automáticamente.
   Si el adaptador rechaza una solicitud inicial ya marcada como pendiente por el motor, este reconcilia el mismo `command_id`, limpia la solicitud y pasa a `FALLO`. Si rechaza una cancelación, reconcilia el ID de la acción original y pasa a `RESULTADO_DESCONOCIDO`; un evento tardío no puede completarla. El motivo queda disponible para bitácora y revisión.
6. «Pausar» es una petición al simulador y no equivale a una parada de emergencia física. La interfaz debe mostrar si la petición fue recibida y si la cancelación terminó.
   Si una finalización compite con una pausa solicitada, v1 conserva `RESULTADO_DESCONOCIDO` para impedir avanzar hasta conciliación simulada; no afirma que la acción se detuvo físicamente.
7. La UI rotula siempre «SIMULACIÓN». Mensajes de ejemplo: «Taladro 101: plan consultado», «Taladro 101: brazo en curso», «Taladro 101: carga simulada completada», «Taladro 101: kg no coincide; revisión requerida».

## Casos mínimos para revisión

| Entrada y contexto | Resultado esperado |
| --- | --- |
| «consultar taladro 101» tras seleccionar 101 | Muestra plan; ninguna solicitud de movimiento. |
| «consultar taladro 102» con 101 seleccionado | Rechazo por ID; selección no cambia. |
| «validar producto alfa, cien kilos» con plan de 100 kg y mismo producto | Marca comparación válida solo si F-09 reconoce exactamente ese valor. |
| «validar producto alfa, 100» | Rechazo por unidad ausente. |
| «no extender brazo» o «extender brazo y cargar» | `unknown/ambiguous`; sin solicitud. |
| «extender brazo» con método manguera o zona ocupada | Rechazo, estado intacto. |
| «confirmar» dos veces | Una sola solicitud. |
| «confirmar» tras vencer o cambiar de taladro | Rechazo; solicitud pendiente descartada. |
| «iniciar carga» antes de movimiento `completed` | Rechazo; no se marca `CARGADO`. |
| «cambiar a modo manual» con acción activa | Rechazo temporal; no hay control simultáneo. |

## Revisión de F-02

- [x] Cada orden del alcance tiene intención, argumentos, precondición, efecto, confirmación y rechazo.
- [x] Los mensajes distinguen reconocimiento, aceptación y fin del simulador.
- [x] Negación, composición, valor/ID/estado dudoso y modo incompatible se rechazan sin acción.
- [ ] Producto, voz, lógica e interfaz validan juntos la tabla antes de fijar código y frases. **Pendiente de revisión del equipo.**

## Implementación integrada de F-22

`faro/confirmation.py` contiene una compuerta determinista integrada por
`FaroController` y `VoicePipeline`: liga token, sesión, modo, taladro, acción,
producto, kg y hora de vencimiento (10 s por defecto). Las acciones críticas no
llegan al simulador hasta confirmar; cancelar, expirar, cambiar contexto,
duplicar o fallar la autorización se rechazan sin envío. La UI muestra el
resumen pendiente y ofrece confirmar/cancelar. La evidencia de voz humana,
usuarios y operación minera sigue siendo pendiente y no se interpreta como
validación industrial.
