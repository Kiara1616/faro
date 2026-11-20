# Faro v1 — revisión de voz, interfaz y QA

**Fecha:** 3 de noviembre de 2026 · **Rol:** revisión independiente de voz local y experiencia de operador · **Ámbito:** F-02, F-04, F-09 y F-13. Este documento evalúa el simulador de laptop. No valida un control industrial ni el desempeño acústico en una MMU real.

## Hallazgo y corrección revisada

**R-01 · Orden contradictorio de validación (alto; corregido en documentos, pendiente en código).** El guion normal de `ALCANCE_Y_DECISIONES.md` colocaba «validar datos» después de solicitar movimiento, mientras `CONTRATO_COMANDOS.md` lo exigía antes. Producto corrigió el guion y el diagrama: consultar plan → preparar → declarar y contrastar producto/kg → confirmar y extender → confirmar y cargar → retraer → cerrar. F-04 y sus pruebas deben demostrar ese orden. Es una hipótesis de simulación; ORICA aún no la ha validado como procedimiento real.

## Riesgos observables y pruebas exigidas

| ID | Riesgo / causa | Prueba reproducible | Resultado exigido | Issue |
| --- | --- | --- | --- | --- |
| V-01 | Vosk con gramática cerrada puede transcribir una frase ajena como una orden admitida. | Reproducir ≥30 frases negativas humanas, conversaciones, radio y silencio con escucha activa; registrar transcripción final. | Informar falsas aceptaciones con denominador; ninguna acción simulada se solicita si parser o contexto rechazan. | F-09, F-11 |
| V-02 | Una frase de conversación se acepta sin prefijo o el prefijo activa captura desde reposo. | Con captura apagada, decir «Oye Faro»; con captura activa, decir conversación, una frase con prefijo en medio, y luego una orden con prefijo. | Desde reposo nada activa captura; las frases sin prefijo/en medio no se registran; la orden con prefijo sí llega al parser. | F-09, F-10 |
| V-03 | El ASR sustituye «cien» por «ciento», «101» por «102» o pierde unidad. | Audio etiquetado de todos los IDs, mezclas y kg del fixture en dos voces; incluir pares cercanos. | Intención/argumentos exactos o rechazo; nunca completar un número faltante con el plan. | F-09, F-11 |
| V-04 | Orden parcial o repetida provoca dos solicitudes. | Emitir transcripción parcial y final idénticas; final duplicado; clic y voz casi simultáneos. | Parcial es solo visual; cada `command_id` se solicita a lo sumo una vez; segunda orden no modifica estado. | F-04, F-10, F-15 |
| V-05 | «Confirmar» se aplica a otra acción o tras cambio de taladro/modo. | Dejar confirmación pendiente, intentar cambiar contexto, esperar vencimiento y confirmar dos veces. | Confirmación ligada a ID, acción, sesión, modo y plan; vencida o repetida no envía. | F-04, F-22 |
| V-06 | El operador interpreta «aceptado» como «terminado». | Inyectar latencia de adaptador; mostrar aceptado y en curso; pedir a dos usuarios qué ocurrió. | Texto «en curso» hasta evento final correcto; mostrar taladro y acción junto al resultado. | F-05, F-13, F-18 |
| V-07 | Desconexión de micrófono conserva indicador de escucha. | Desconectar o simular error del dispositivo tras empezar; pulsar F8 otra vez. | Estado visible «micrófono no disponible»; no procesar voz; reintento explícito sin doble hilo. | F-25, F-13 |
| V-08 | Cambio a manual mientras hay ejecución o captura abierta. | Solicitar modo manual durante carga/movimiento; repetir tras detener escucha. | Transferencia bloqueada durante acción activa; al permitirla, micrófono detenido y modo auditado. | F-07, F-13 |
| V-09 | Negación o frases compuestas se parecen a orden. | «No extender brazo», «extender brazo y cargar», «creo que hay que cargar». | `unknown/ambiguous`, motivo visible, cero solicitud. | F-02, F-09 |
| V-10 | Error o timeout deja un estado visual engañoso. | Inyectar fallo, timeout, evento tardío y evento con ID distinto. | Nunca «completado» sin evento final correlacionado; mostrar revisión necesaria. | F-04, F-13, F-23 |

## Contrato mínimo para F-04 desde la interfaz

La decisión del motor debe exponer `command_id`, `intent`, argumentos, `state_before`, `state_after`, `accepted`, `reason` y `message`. Un estado de tarea y un estado de ejecución separados ayudan a mostrar que «confirmación pendiente» y «en curso» no equivalen a «cargado». Cada rechazo debe conservar el estado operacional, aunque añada un evento de auditoría. Una lectura del plan puede actualizar la vista; eso no es una acción de la MMU simulada.

**Pruebas mínimas del dominio:** ciclo completo por los taladros 101 y 102; selección errónea 999; 103 bloqueado; extender antes de consultar o validar; método equivocado; zona ficticia ocupada; repetición; acción concurrente; cambio de taladro durante acción; evento final de ID ajeno. F-04 puede probar reglas sin micrófono con intenciones tipadas. F-09 probará la transformación de frase a intención; F-15 verificará los componentes juntos.

## Vocabulario y respuesta de voz de F-09/F-13

Usar frases canónicas breves con verbo y objeto: «seleccionar taladro 101», «consultar taladro 101», «preparar carga», «validar producto alfa, cien kilos», «extender brazo», «iniciar carga», «retraer brazo», «cerrar taladro». El parser debe exigir la frase completa y unidad de kg. Las variantes habladas se enumeran y prueban, no se aceptan por similitud. La gramática de Vosk puede mejorar reconocimiento, pero no es una barrera de autorización.

La UI debe mostrar al mismo tiempo: **taladro activo**, **plan**, **transcripción final**, **intención interpretada**, **estado del comando** y **resultado del simulador**. Un mensaje de confirmación debe nombrar taladro y acción. Ejemplos: «Taladro 101: ¿confirmar extensión de brazo?» y luego «Taladro 101: extensión en curso»; solo tras el evento: «Taladro 101: brazo extendido en la simulación». Si falla, «Taladro 101: no se completó; revisar estado». El color complementa texto e icono; el rótulo «SIMULACIÓN» permanece visible.

## Evidencia para la revisión final

- [ ] Se corrigió R-01 en alcance, matriz y guion, y la misma secuencia se refleja en tests.
- [ ] F-04 cubre transiciones válidas y prohibidas con snapshots antes/después; QA revisó los rechazos.
- [ ] F-09 muestra tabla de al menos 20 frases positivas y 30 negativas, con IDs y kg del fixture.
- [ ] F-11 reporta voces, condiciones, tamaño de muestra, falsas aceptaciones y latencia por separado.
- [ ] F-13 se ensayó con demora, fallo, timeout y pérdida de micrófono; un usuario puede distinguir «escuchado» de «completado».

La aceptación de estas pruebas certifica solo el comportamiento del **prototipo simulado** bajo las condiciones ensayadas. Cualquier validación para operación minera requeriría requisitos, datos y revisión competente de ORICA.

## Revisión específica de F-07: sesión, fuente y modo

Al revisar `faro/domain.py` durante F-04, el motor todavía recibe una `Command` tipada sin `source`, `session_id`, modo o estado real de escucha. Esto delimita correctamente el núcleo de transiciones de F-04, pero **no cumple F-07** por sí solo. El controlador de sesión debe ser una frontera obligatoria antes de llamar a `FaroDomain.handle`; ni la UI ni un callback del ASR pueden saltársela.

| Caso | Estado inicial | Entrada | Resultado exigido |
| --- | --- | --- | --- |
| Voz en manual | Sesión ficticia activa, modo `MANUAL` | `source=voice`, cualquier intención, incluso consulta | Rechazo auditado; cero llamadas al dominio para acciones y cero solicitudes al adaptador. |
| Voz con escucha apagada | Modo `VOZ`, captura detenida | Resultado tardío del hilo de voz | Rechazo por generación/sesión de escucha inválida; no ejecuta. |
| Manual durante acción | Solicitud pendiente del dominio | Cambiar a `MANUAL` | No cambiar modo ni activar entrada manual; mostrar acción pendiente. |
| Transferencia válida | Sin acción pendiente, modo `VOZ` | Desactivar voz, esperar cierre confirmado de captura, cambiar a `MANUAL` | Modo visible y auditado; cualquier callback antiguo queda invalidado. |
| Retorno a voz | Modo `MANUAL`, micrófono/modelo disponible | Cambiar a `VOZ` | La escucha permanece apagada hasta botón/F8; ninguna frase por sí sola la inicia. |
| Otra sesión | Una confirmación o resultado asociado a sesión anterior | Resultado tardío o «confirmar» de sesión nueva | No autoriza ni completa la orden anterior; correlacionar `session_id` y `command_id`. |
| Identidad ficticia | Sesión con ID y nombre de prueba | Voz de otra persona | El prototipo no puede atribuir autoría biométrica; la UI/bitácora debe decir «sesión de prueba» y no «voz verificada». |

**Punto de integración:** el origen de la orden debe provenir del adaptador de entrada, no de texto que pueda pronunciarse. Una transcripción que diga «cambiar a modo manual» sigue siendo `source=voice`. El cambio requiere apagar captura y comprobar su cierre para evitar órdenes tardías. Si esa operación falla o expira, mantener el modo anterior o `DESHABILITADO` con mensaje explícito; nunca mostrar ambos canales habilitados.

F-07 implementa esta frontera con `session_id`, `mode`, `listening` y `generation`. La entrada `text` solo representa un control manual de prueba explícito; no habilita el micrófono. La revisión final aún debe comprobar que UI, ASR y bitácora usen esta frontera, no llamadas directas a `handle`.
