# Faro — backlog de issues para el Reto 3 ORICA

**Actualización al 3 de noviembre de 2026; entrega el 10 de noviembre.** El estado de cada issue se consulta en GitHub. `P0` bloquea la versión integrada; `P1` completa la calidad profesional de v1 y no se elimina por la fecha de entrega. Las personas del equipo pueden escribir su nombre junto al rol. El [plan y calendario](PLAN_FARO_ORICA.md) contienen las puertas de salida de cada hito.

**Roles de revisión:** producto contrasta el briefing y los supuestos; lógica y seguridad del simulador comprueban estados e invariantes; voz valida transcripción y falsas aceptaciones; interfaz comprueba comprensión; integración revisa contratos, persistencia y empaquetado; QA reproduce casos positivos y adversos. Son responsabilidades del equipo de software. La validación de operación minera y de controles de una MMU real corresponde a ORICA en una fase autorizada.

**Regla de cierre:** asignar una persona implementadora y otra revisora; enlazar código, resultado de prueba y evidencia visual o registro según el issue. Marcar las tres casillas de revisión antes de cerrar. Una prueba manual no sustituye una prueba automatizada cuando el issue exige ambas.

| ID | Hito | Prioridad | Título | Responsable sugerido | Depende de |
| --- | --- | --- | --- | --- | --- |
| F-01 | M0 | P0 | Cerrar alcance y registrar decisiones | Producto/integración | — |
| F-02 | M0 | P0 | Matriz de órdenes y condiciones de rechazo | Lógica + producto | F-01 |
| F-03 | M0 | P0 | Malla y datos ficticios reproducibles | Lógica | F-01 |
| F-04 | M1 | P0 | Motor de estados del ciclo por taladro | Lógica | F-02, F-03 |
| F-05 | M1 | P0 | Adaptador de MMU simulada y eventos | Lógica/integración | F-04 |
| F-06 | M1 | P0 | Excepciones de taladro, cantidad y mezcla | Lógica | F-04, F-05 |
| F-07 | M1 | P0 | Sesión y modos voz/manual excluyentes | Integración | F-02, F-04 |
| F-08 | M1 | P0 | Bitácora de decisiones y resultados | Integración | F-04, F-05 |
| F-09 | M2 | P0 | Vocabulario de Faro y análisis de números | Voz + lógica | F-02, F-03 |
| F-10 | M2 | P0 | Conectar ASR local al nuevo dominio | Voz | F-09, F-04 |
| F-11 | M2 | P0 | Corpus y evaluación de voz | Voz/QA | F-09, F-10 |
| F-12 | M3 | P0 | Consola de operación por taladro | Interfaz | F-01, F-03 |
| F-13 | M3 | P0 | Estados de ejecución y alertas claras | Interfaz | F-05, F-06, F-12 |
| F-14 | M3 | P1 | Confirmaciones breves y ergonomía | Interfaz + voz | F-12, F-13 |
| F-15 | M4 | P0 | Integración completa voz–reglas–simulador–UI | Integración | F-07, F-08, F-10, F-13, F-22, F-23 |
| F-16 | M4 | P0 | Arranque reproducible sin Internet | Integración | F-15 |
| F-17 | M5 | P0 | Matriz de fallos y métricas de aceptación | QA + todos | F-11, F-15, F-16 |
| F-18 | M5 | P1 | Prueba de comprensión con usuarios del equipo | Producto/interfaz | F-15 |
| F-19 | M6 | P0 | Guion, evidencia y pitch de 5 minutos | Producto + todos | F-17 |
| F-20 | M6 | P0 | Congelar versión y verificar entrega | Integración + todos | F-16, F-17, F-19, F-27, F-28 |
| F-21 | M0 | P0 | Invariantes y alcance de seguridad del simulador | Producto + lógica | F-01, F-02 |
| F-22 | M1 | P0 | Confirmación, pausa y cancelación simuladas | Lógica + interfaz | F-04, F-21 |
| F-23 | M1 | P0 | Timeout, eventos tardíos y recuperación | Lógica/integración | F-05, F-21 |
| F-24 | M1 | P0 | Escenarios reproducibles e inyección de fallos | Lógica/QA | F-03, F-05 |
| F-25 | M2 | P0 | Fallos de audio y estado real de escucha | Voz/integración | F-10 |
| F-26 | M4 | P1 | Privacidad de transcripciones y exportación de evidencia | Integración | F-08 |
| F-27 | M4 | P0 | Paquete offline verificable para Windows | Integración | F-16 |
| F-28 | M5 | P0 | Pruebas integradas y puerta de calidad en CI | QA/integración | F-15, F-22, F-23, F-24 |
| F-29 | M6 | P0 | Manifiesto de entrega y traspaso | Producto/integración | F-17, F-20 |

## M0 — Alcance y contrato (2–3 nov.)

### F-01 · Cerrar alcance y registrar decisiones

**Objetivo:** traducir las respuestas del briefing a un contrato de producto y separar hechos de propuestas.
**Trabajo:** definir operador, taladro, plan, acciones, estados, mensajes y alcance del simulador. Abrir una lista de preguntas para ORICA mediante el comité; registrar respuesta, fecha y efecto en el alcance.
**Cierre:** existe un diagrama de un ciclo por taladro, una lista de supuestos explícitos y un guion de caso normal y excepcional que el equipo puede explicar sin contradicciones.

**Entregable verificable:** planning/ALCANCE_Y_DECISIONES.md, diagrama de ciclo y registro de preguntas a ORICA por el comité.

**Criterios de aceptación detallados:** Distinguir en cada decisión hecho del briefing, supuesto del equipo y pendiente; trazar un caso normal y uno excepcional; no atribuir aprobación técnica a ORICA.

**Evidencia para cerrar:** Revisión cruzada con Analisis_briefing_Faro_ORICA_2026-10-28.md; enlace al documento y acta breve del equipo.

**Revisión antes de entregar — Producto:**
- [ ] Implementación: Mapear cada afirmación del briefing a tiempo/fuente y anotar supuestos.
- [ ] Casos adversos: Revisar que una respuesta futura de ORICA tenga dueño y efecto previsto en el alcance.
- [ ] Revisión final: Leer el flujo con otra persona y señalar cualquier paso sin origen o decisión registrada.

### F-02 · Matriz de órdenes y condiciones de rechazo

**Objetivo:** que cada orden tenga una intención, precondiciones y salida definida.
**Trabajo:** construir tabla para `consultar taladro`, `extender/retraer brazo`, `extender/retraer manguera`, `preparar carga`, `pausar`, `consultar estado`, `cerrar taladro` y `siguiente taladro`. Marcar cuáles son solo simuladas, qué datos exigen y qué ocurre ante micrófono, estado o sensor ficticio adverso.
**Cierre:** toda orden tiene estados permitidos/prohibidos, mensaje de rechazo y evento de auditoría; ninguna frase desconocida se convierte en acción por similitud.

**Entregable verificable:** planning/CONTRATO_COMANDOS.md con intención, parámetros, fuente, estados, confirmación, rechazo y mensaje por orden.

**Criterios de aceptación detallados:** Cubrir consulta, selección, brazo, manguera, carga, pausa, cierre, siguiente y modo; número o unidad ausente, negación y frase desconocida no producen acción.

**Evidencia para cerrar:** Revisión conjunta de voz/lógica/UI; una prueba positiva y una negativa por intención.

**Revisión antes de entregar — Producto + voz:**
- [ ] Implementación: Enumerar entradas exactas, argumentos, estados y efectos de todas las intenciones.
- [ ] Casos adversos: Probar frase compuesta, negación, dato ausente y comando de otro taladro.
- [ ] Revisión final: Comparar tabla con parser, motor y mensajes; ningún botón o voz omite la validación.

### F-03 · Malla y datos ficticios reproducibles

**Objetivo:** tener un escenario coherente antes de diseñar pantallas.
**Trabajo:** crear una malla local de al menos 3 taladros con ID, mezcla, cantidad prevista, método de entrega y estado. Incluir un taladro normal, uno con discrepancia y uno bloqueado. Identificar todos los datos como simulados.
**Cierre:** el mismo archivo o semilla genera el mismo recorrido y no contiene diseños ni cantidades operacionales de ORICA.

**Entregable verificable:** Fixture JSON versionado de tres taladros y validador de esquema.

**Criterios de aceptación detallados:** IDs únicos, producto, kg y método explícitos; casos normal, divergente y bloqueado; archivo incompleto o duplicado falla antes de iniciar; datos rotulados ficticios.

**Evidencia para cerrar:** Tests de fixture válido, ID duplicado, campo ausente, kg inválidos y carga repetible.

**Revisión antes de entregar — Producto + QA:**
- [ ] Implementación: Definir esquema, versión y tres taladros ficticios con unidades visibles.
- [ ] Casos adversos: Rechazar duplicados, kg no positivos, producto o método desconocido.
- [ ] Revisión final: Confirmar que cada fixture se reinicia igual y no contiene datos de ORICA.

### F-21 · Invariantes y alcance de seguridad del simulador

**Objetivo:** Escribir las reglas que nunca debe violar v1 en cualquier canal.

**Trabajo:** Definir una acción activa, rechazo sin mutación, taladro/kg/mezcla validados antes de carga, zona ficticia despejada antes de movimiento, exclusión voz/manual y completado solo tras evento final. Diferenciar pausa simulada de parada física de emergencia, que no se implementa.

**Cierre:** Cada invariante tiene prueba negativa y mensaje; controles ficticios y pendientes de ORICA se identifican como tales.

**Entregable verificable:** planning/INVARIANTES.md, tabla regla → prueba → resultado.

**Evidencia para cerrar:** Revisión de lógica/producto antes de cerrar motor, confirmación y timeouts.

**Revisión antes de entregar — Seguridad + producto:**
- [ ] Implementación: Escribir invariantes como condiciones comprobables y riesgos del simulador.
- [ ] Casos adversos: Incluir rechazo sin mutación, una acción, zona ocupada y fin confirmado.
- [ ] Revisión final: Rastrear cada invariante a test; distinguir pausa simulada de paro físico.

## M1 — Dominio y MMU simulada (3–5 nov.)

### F-04 · Motor de estados del ciclo por taladro

**Objetivo:** sustituir la revisión auxiliar ficticia actual.
**Trabajo:** implementar estados como `sin selección → taladro consultado → preparado → acción en curso → carguío simulado → cerrado → siguiente`, con transiciones explícitas y cancelación. Mantener el motor separado de Qt y del ASR.
**Cierre:** pruebas unitarias cubren un ciclo válido, órdenes fuera de orden, repetición y cambio de taladro durante una acción.

**Entregable verificable:** Modelos tipados, tabla de transiciones y motor independiente de Qt y ASR.

**Criterios de aceptación detallados:** Ciclo por teclado de selección a cierre; fuera de secuencia, orden repetida y cambio de taladro durante acción no avanzan; decisión conserva estado antes/después e ID.

**Evidencia para cerrar:** Tests de camino feliz y cada transición prohibida; revisar que rechazo no muta estado operacional.

**Revisión antes de entregar — Seguridad + QA:**
- [ ] Implementación: Codificar estados y transiciones sin dependencia de la interfaz.
- [ ] Casos adversos: Inyectar orden simultánea, repetida y cambio de taladro con acción pendiente.
- [ ] Revisión final: Inspeccionar snapshots antes/después y probar que cada rechazo conserva el estado.

### F-05 · Adaptador de MMU simulada y eventos

**Objetivo:** probar la diferencia entre una orden aceptada y una acción concluida.
**Trabajo:** definir una interfaz interna para solicitar acciones y recibir `aceptada`, `en curso`, `completada`, `fallida` o `cancelada`. Implementar respuestas tardías y fallo inyectable; ninguna salida física o de red.
**Cierre:** la UI no puede mostrar «completado» antes del evento correspondiente y una acción fallida no cambia el estado final a éxito.

**Entregable verificable:** Contrato de adaptador y simulador con demora, fallo y eventos correlacionados por command_id.

**Criterios de aceptación detallados:** Enviar no equivale a completar; evento duplicado, tardío o de otro ID no cambia estado; no hay sockets, puertos industriales ni salidas físicas.

**Evidencia para cerrar:** Tests de aceptación, demora, finalización, fallo, evento duplicado e ID ajeno.

**Revisión antes de entregar — Seguridad + integración:**
- [ ] Implementación: Separar respuesta de aceptación, progreso y fin por command_id.
- [ ] Casos adversos: Inyectar evento duplicado, desordenado, perdido y de ID distinto.
- [ ] Revisión final: Comprobar que solo un evento final válido permite mostrar completado.

### F-06 · Excepciones de taladro, cantidad y mezcla

**Objetivo:** reflejar los desvíos de campo mencionados por ORICA sin inventar autorización.
**Trabajo:** detectar ID distinto, cantidad/mezcla divergente, taladro bloqueado, método incompatible o dato faltante. Crear una alerta separada sin mutar el estado operativo rechazado y registrar causa, plan y valor recibido. ID/dato/método erróneo generan alerta transitoria y permiten corregir la entrada; producto o kg divergentes generan alerta bloqueante del taladro hasta una declaración ficticia completa y exacta. Un taladro bloqueado se rechaza al seleccionarlo y permite elegir otro.
**Cierre:** cada excepción se reproduce con un caso y queda claro en pantalla si se requiere revisión humana. El prototipo no trata un «sí» de voz como autorización industrial.

**Entregable verificable:** Alertas y mensajes de excepción para ID, kg, mezcla, dato faltante, bloqueo y método, con ruta de resolución por causa.

**Criterios de aceptación detallados:** Ninguna discrepancia alcanza cargado; se ve plan y valor recibido; un sí de voz no autoriza cambio; corrección ficticia no reanuda orden antigua.

**Evidencia para cerrar:** Test por desviación y de recuperación; bitácora contiene causa y decisión.

**Revisión antes de entregar — Producto + QA:**
- [ ] Implementación: Definir causa, mensaje y ruta ficticia de corrección para cada desvío.
- [ ] Casos adversos: Combinar discrepancias de ID, mezcla y kg; probar dato vacío y taladro bloqueado.
- [ ] Revisión final: Verificar que nunca se inicia carga con excepción pendiente ni se borra el plan original.

### F-07 · Sesión y modos voz/manual excluyentes

**Objetivo:** modelar al operador responsable y evitar órdenes simultáneas.
**Trabajo:** añadir identidad ficticia de sesión y modos `voz`, `manual` y `deshabilitado`. Al fallar el ASR, permitir detener la escucha y pasar explícitamente al modo manual simulado.
**Cierre:** los comandos hablados se rechazan en modo manual; no hay dos acciones activas; una transferencia queda registrada. La sesión no se presenta como biometría por voz.

**Entregable verificable:** Modelo de sesión ficticia, estados voz/manual/deshabilitado y controles de cambio.

**Criterios de aceptación detallados:** Voz en manual se rechaza; detener escucha antes de transferencia; cambio durante acción no la completa; una sola acción activa; sesión no se presenta como biometría.

**Evidencia para cerrar:** Tests de transferencias y entrada simultánea voz/teclado; captura del modo visible.

**Revisión antes de entregar — Seguridad + voz:**
- [ ] Implementación: Definir estados de sesión y transferencia de voz a manual.
- [ ] Casos adversos: Intentar voz en manual, cambio en medio de acción y entradas simultáneas.
- [ ] Revisión final: Corroborar que micrófono, modo visible, motor y bitácora coincidan.

### F-08 · Bitácora de decisiones y resultados

**Objetivo:** reconstruir qué se dijo, qué se decidió y qué sucedió.
**Trabajo:** ampliar SQLite para guardar hora, operador ficticio, fuente, transcripción, intención, taladro, estado anterior, decisión, motivo y evento final. Migrar la estructura existente o crear una nueva versión sin perder arranque.
**Cierre:** la secuencia de un caso exitoso y uno rechazado puede consultarse tras reiniciar; no se almacena audio crudo.

**Entregable verificable:** Esquema SQLite versionado, migración desde decisions actual y consulta por command_id.

**Criterios de aceptación detallados:** Persisten hora UTC, sesión, fuente, transcripción, intención, taladro, estados, decisión, motivo y eventos; no audio; reinicio reconstruye éxito y rechazo.

**Evidencia para cerrar:** Test con BD anterior temporal, reinicio y correlación de evento tardío.

**Revisión antes de entregar — QA + integración:**
- [ ] Implementación: Versionar esquema y documentar migración desde la BD actual.
- [ ] Casos adversos: Reiniciar tras éxito, rechazo y acción incompleta; probar BD anterior.
- [ ] Revisión final: Reconstruir secuencia por ID y confirmar que no se guardó audio.

### F-22 · Confirmación, pausa y cancelación simuladas

**Objetivo:** Evitar que una frase incompleta, caducada o repetida desencadene una acción.

**Trabajo:** Definir en el contrato qué movimiento/carga requiere confirmación; mostrar resumen de taladro, acción, producto y kg cuando aplique; ventana temporal; cancelar descarta; pausar interrumpe según estado. Es una regla de prototipo, no política de ORICA.

**Cierre:** Confirmación vencida, de otro taladro o con datos cambiados no ejecuta; repetición no duplica; cancelación queda auditada.

**Entregable verificable:** Estado pending_confirmation, temporizador y mensajes.

**Evidencia para cerrar:** Tests de confirmar, rechazar, vencer, repetir y cambiar contexto.

**Revisión antes de entregar — Seguridad + interfaz:**
- [ ] Implementación: Definir confirmación por acción, contenido, vencimiento y cancelación.
- [ ] Casos adversos: Probar confirmación duplicada, tardía y tras cambio de taladro/plan.
- [ ] Revisión final: Inspeccionar que solicitud al simulador ocurre solo tras confirmación válida.

### F-23 · Timeout, eventos tardíos y recuperación

**Objetivo:** Mantener estado conservador si el simulador no responde o la app se interrumpe.

**Trabajo:** Fijar timeout configurable de prototipo; una solicitud sin respuesta pasa a desconocido/requiere revisión y bloquea órdenes dependientes. Al reiniciar, no reenviar automáticamente. Correlacionar eventos tardíos y duplicados por ID.

**Cierre:** La demora no aparece completada; reinicio no infiere éxito; evento tardío no completa otra orden; la recuperación manual simulada es visible.

**Entregable verificable:** Política de timeout/reinicio y código con reloj inyectable.

**Evidencia para cerrar:** Tests deterministas de timeout, reinicio, duplicado y evento tardío.

**Revisión antes de entregar — Seguridad + QA:**
- [ ] Implementación: Definir reloj inyectable, timeout y estado de recuperación conservador.
- [ ] Casos adversos: Probar reinicio, respuesta tardía y evento repetido.
- [ ] Revisión final: Verificar que no se reenvía automáticamente ni se infiere éxito.

### F-24 · Escenarios reproducibles e inyección de fallos

**Objetivo:** Repetir guion y fallos sin modificar el código.

**Trabajo:** Versionar escenarios de zona ficticia ocupada, taladro bloqueado, fallo de brazo/manguera, demora y rechazo del adaptador; selector rotulado simulación; reinicio de semilla.

**Cierre:** Cada escenario produce igual resultado dos veces y deja eventos auditables; el modo normal no hereda fallos anteriores.

**Entregable verificable:** Fixtures, cargador y guía de reproducción.

**Evidencia para cerrar:** Tests por fixture y ensayo manual de reinicio.

**Revisión antes de entregar — QA + producto:**
- [ ] Implementación: Versionar fixtures y selector visible de escenario ficticio.
- [ ] Casos adversos: Ejecutar cada fallo dos veces y luego volver al escenario normal.
- [ ] Revisión final: Comparar eventos y estado final; no debe quedar contaminación entre ensayos.

## M2 — Canal de voz local (3–6 nov.)

### F-09 · Vocabulario de Faro y análisis de números

**Objetivo:** tener órdenes cortas y pronunciables para el caso real.
**Trabajo:** fijar frases canónicas y variantes limitadas; reconocer IDs de taladro y kilos en palabras o cifras sin inferir valores ambiguos. Permitir `Oye Faro` como prefijo con escucha activa. Reservar una frase de activación continua para investigación posterior.
**Cierre:** tabla de al menos 20 frases positivas y 30 negativas; cada frase esperada tiene intención/argumentos inequívocos; valores dudosos se rechazan.

**Entregable verificable:** Parser determinista y tabla de al menos 20 frases positivas y 30 negativas.

**Criterios de aceptación detallados:** Cada positivo da intención y argumentos exactos; negación, dos acciones, valor dudoso, unidad faltante o frase ajena se rechazan; Oye Faro solo es prefijo con escucha activa.

**Evidencia para cerrar:** Tests parametrizados de acentos, cifras/palabras, IDs, kg, unidades y negativos.

**Revisión antes de entregar — Seguridad + QA:**
- [ ] Implementación: Fijar gramática cerrada con unidades, IDs y números explícitos.
- [ ] Casos adversos: Probar homófonos, números cercanos, dos órdenes, negaciones y prefijo aislado.
- [ ] Revisión final: Comparar intención/argumentos exactos; ninguna aproximación dispara acción.

### F-10 · Conectar ASR local al nuevo dominio

**Objetivo:** reutilizar Vosk y el micrófono existentes para el flujo por taladro.
**Trabajo:** integrar transcripciones con el analizador de F-09 y el motor de F-04, mantener botón/F8 y selección de dispositivo. Mostrar error de micrófono y pérdida de escucha.
**Cierre:** un ciclo por taladro puede hacerse con voz en audio limpio sin Internet; comandos desconocidos no producen una acción.

**Entregable verificable:** Integración Vosk local → parser → motor y estados visibles de escucha.

**Criterios de aceptación detallados:** Completar ciclo limpio sin Internet; resultado parcial/final no duplica acción; frase desconocida no cambia estado; hilo de UI responde durante reconocimiento.

**Evidencia para cerrar:** Tests con transcripciones y ensayo documentado con micrófono, dispositivo y entorno.

**Revisión antes de entregar — Lógica + QA:**
- [ ] Implementación: Conectar transcripción final al parser y conservar la parcial solo para visualización.
- [ ] Casos adversos: Probar micrófono activo/inactivo, repetición de final y frase no admitida.
- [ ] Revisión final: Verificar que UI no se congela y no hay llamada directa del ASR al adaptador.

### F-11 · Corpus y evaluación de voz

**Objetivo:** medir reconocimiento y falsas aceptaciones en condiciones identificadas.
**Trabajo:** ampliar el evaluador existente con al menos 2 personas del equipo, frases de comandos, nombres/IDs, números, conversaciones parecidas y ruido reproducido por separado. Reportar por caso transcripción, decisión y latencia.
**Cierre:** informe con denominadores, condiciones y errores; se distingue audio sintético de humano. Las metas de prototipo del plan se evalúan y cualquier incumplimiento queda documentado.

**Entregable verificable:** Corpus local consentido, manifiesto de casos y reporte de métricas por condición.

**Criterios de aceptación detallados:** Al menos dos voces humanas; separar audio limpio, ruido reproducido y sintético; reportar denominadores, falsas aceptaciones, p50/p95 y cada meta no lograda.

**Evidencia para cerrar:** Repetir evaluación con mismo corpus; revisar manualmente falsos positivos; no publicar WAV privados.

**Revisión antes de entregar — Producto + QA:**
- [ ] Implementación: Etiquetar voces consentidas, comando esperado, contexto y condiciones de ruido.
- [ ] Casos adversos: Contabilizar falsas aceptaciones por acción y números confundidos.
- [ ] Revisión final: Recalcular denominadores y latencia; publicar limitaciones de tamaño de muestra.

### F-25 · Fallos de audio y estado real de escucha

**Objetivo:** Evitar que la UI afirme escuchar tras fallo de captura.

**Trabajo:** Detectar modelo ausente, dispositivo inválido, desconexión, permisos y fallo del hilo; cerrar recursos, bloquear voz y ofrecer reconexión explícita. Entrada escrita sigue disponible.

**Cierre:** Cada fallo muestra no disponible/detenido; F8 refleja estado real; reintento no crea dos hilos ni decisiones.

**Entregable verificable:** Estados de captura, mensajes y ruta de recuperación.

**Evidencia para cerrar:** Tests con dispositivo simulado y ensayo de desconexión de micrófono.

**Revisión antes de entregar — Integración + QA:**
- [ ] Implementación: Modelar estados reales de captura y mensajes de recuperación.
- [ ] Casos adversos: Simular permiso denegado, dispositivo perdido, modelo faltante y reintento.
- [ ] Revisión final: Confirmar cierre de hilo y ausencia de decisiones duplicadas tras reconectar.

## M3 — Consola operacional (3–6 nov.)

### F-12 · Consola de operación por taladro

**Objetivo:** reemplazar la UI de temperatura/presión/batería por una pantalla útil para el caso.
**Trabajo:** mostrar malla ficticia, taladro activo, mezcla y kilos previstos, método de entrega, estado de brazo/manguera, modo de control y último comando. Mantener diseño formal y legible a distancia de laptop.
**Cierre:** una captura de pantalla permite identificar en pocos segundos taladro, plan, estado y si se trata de una simulación.

**Entregable verificable:** Consola Qt por taladro con malla, plan, método, brazo/manguera, modo, escucha y último resultado.

**Criterios de aceptación detallados:** Una captura identifica taladro, plan, estado y simulación; dos taladros se recorren sin cambiar de ventana; UI solo emite intenciones.

**Evidencia para cerrar:** Prueba Qt offscreen y recorrido manual de tres fixtures con captura.

**Revisión antes de entregar — Producto + QA:**
- [ ] Implementación: Trazar cada dato visual a plan, motor o simulador; rotular simulación.
- [ ] Casos adversos: Mostrar estado sin taladro, excepción y acción pendiente.
- [ ] Revisión final: Revisar captura a distancia de laptop y navegar dos taladros por teclado.

### F-13 · Estados de ejecución y alertas claras

**Objetivo:** impedir que el operador confunda una transcripción con una acción finalizada.
**Trabajo:** visualizar `escuchado`, `interpretado`, `validando`, `en curso`, `completado`, `rechazado` y `requiere revisión`, más motivo preciso. Evitar colores como única señal.
**Cierre:** casos de demora, rechazo y fallo del simulador se distinguen visualmente y aparecen en la bitácora.

**Entregable verificable:** Tabla evento → mensaje y componentes para escuchado, interpretado, pendiente, en curso, completado, rechazado, fallido y revisión.

**Criterios de aceptación detallados:** Demora permanece en curso; fallo y rechazo se distinguen sin depender solo del color; evento de otro ID no cambia la vista; bitácora y pantalla concuerdan.

**Evidencia para cerrar:** Pruebas UI de demora, fallo, rechazo, excepción y correlación.

**Revisión antes de entregar — Seguridad + QA:**
- [ ] Implementación: Definir texto y severidad por evento, sin usar color como único indicador.
- [ ] Casos adversos: Probar progreso prolongado, fallo, rechazo, timeout y evento ajeno.
- [ ] Revisión final: Comparar texto final con estado del motor y registro por ID.

### F-14 · Confirmaciones breves y ergonomía

**Objetivo:** dar retroalimentación útil sin saturar la cabina.
**Trabajo:** redactar mensajes cortos con ID de taladro y resultado. Evaluar TTS local únicamente para lectura de estado y confirmaciones; si suena confuso o retrasa el flujo, dejar respuesta visual. Revisar tamaños de fuente, contraste y uso con auricular.
**Cierre:** la prueba con miembros del equipo permite repetir correctamente qué acción se completó y cuál falló; TTS no se usa como prueba de seguridad.

**Entregable verificable:** Catálogo de mensajes breves con ID/acción/resultado y checklist de ergonomía.

**Criterios de aceptación detallados:** Dos usuarios pueden repetir qué terminó y qué se rechazó; resultado sigue visible si TTS falla; teclado, contraste y tamaño legibles en laptop/auricular.

**Evidencia para cerrar:** Ensayo de comprensión y captura de estados; registrar decisión de incluir o no TTS local.

**Revisión antes de entregar — Producto + voz:**
- [ ] Implementación: Redactar mensajes cortos con taladro y resultado explícitos.
- [ ] Casos adversos: Evaluar foco, tamaño, contraste y salida TTS opcional con auricular.
- [ ] Revisión final: Pedir a dos usuarios que expliquen qué pasó sin ver el código.

## M4 — Integración y empaquetado (6–8 nov.)

### F-15 · Integración completa voz–reglas–simulador–UI

**Objetivo:** unir componentes con un solo flujo de eventos y sin atajos desde la UI al simulador.
**Trabajo:** conectar señales de voz, analizador, motor, adaptador y bitácora; evitar dobles órdenes por clic/voz simultáneos; incluir fallos inyectables para la demostración.
**Cierre:** guion de dos taladros consecutivos funciona por voz y teclado; el resultado visual coincide con el estado y la bitácora.

**Entregable verificable:** Composición ASR-parser-motor-adaptador-auditoría-UI y guion técnico.

**Criterios de aceptación detallados:** Dos taladros consecutivos por voz o texto; rechazo no llama al adaptador; clic/voz simultáneos no duplican comando; SQLite, UI y motor coinciden.

**Evidencia para cerrar:** Tests de integración sin hardware y recorrido manual en laptop.

**Revisión antes de entregar — Seguridad + QA:**
- [ ] Implementación: Integrar componentes por contratos y serializar solicitudes.
- [ ] Casos adversos: Correr voz y clic casi simultáneos; provocar rechazo antes de adaptador.
- [ ] Revisión final: Comparar UI, motor y SQLite en dos taladros; una intención produce a lo sumo una solicitud.

### F-16 · Arranque reproducible sin Internet

**Objetivo:** ejecutar Faro en la laptop disponible sin instalaciones de último momento.
**Trabajo:** fijar dependencias, verificar modelo Vosk local, carpeta de datos, elección de micrófono, script de inicio y recuperación ante micrófono ausente. Mantener Docker como entorno de pruebas sin interfaz y verificar CI en Windows. Documentar un procedimiento de instalación y uno de ejecución.
**Cierre:** desde una copia limpia preparada, el programa arranca, completa el guion y se reinicia sin red; no depende de nube ni de servicios externos.

**Entregable verificable:** Guía de instalación y arranque, versiones fijadas, diagnóstico local y checklist offline.

**Criterios de aceptación detallados:** Copia limpia preparada inicia, completa guion y reinicia sin red; falta de modelo/malla/micrófono da mensaje útil; Docker solo prueba código sin GUI.

**Evidencia para cerrar:** CI Windows, ensayo con red desactivada y registro de versión de Python/Windows.

**Revisión antes de entregar — QA + integración:**
- [ ] Implementación: Fijar dependencias, modelo local, rutas de datos y diagnóstico de inicio.
- [ ] Casos adversos: Probar modelo ausente, ruta con espacios y red desactivada.
- [ ] Revisión final: Seguir guía en copia limpia y registrar versión de Windows/Python.

### F-26 · Privacidad de transcripciones y exportación de evidencia

**Objetivo:** Conservar trazabilidad sin divulgar voces ni datos privados de ensayo.

**Trabajo:** Definir ubicación, acceso y limpieza de SQLite; exportar reporte ficticio de decisiones/eventos sin audio; revisar .gitignore y paquete para excluir BD, WAV, briefing y secretos; documentar consentimiento del corpus.

**Cierre:** Evidencia presentable sin audio humano ni datos personales; carpeta de entrega no contiene ensayos no autorizados.

**Entregable verificable:** Política breve, comando de exportación/limpieza y reporte ficticio.

**Evidencia para cerrar:** Pruebas de exportación/borrado y revisión de archivos rastreados y empaquetados.

**Revisión antes de entregar — Producto + QA:**
- [ ] Implementación: Definir conservación, limpieza y reporte exportable con datos ficticios.
- [ ] Casos adversos: Revisar .gitignore, carpeta de entrega y BD tras ensayo humano.
- [ ] Revisión final: Otro integrante inspecciona que no haya WAV, datos personales ni briefing privado.

### F-27 · Paquete offline verificable para Windows

**Objetivo:** Entregar carpeta ejecutable comprobable en la laptop prevista.

**Trabajo:** Empaquetar app, dependencias, modelo local permitido, malla ficticia, guía y diagnóstico. Crear manifiesto de versiones y hashes; probar rutas con espacios; no presuponer administrador o instalador.

**Cierre:** Otro integrante abre carpeta sin red y recorre caso normal/fallo; falta o hash incorrecto de asset esencial se detecta al inicio.

**Entregable verificable:** Carpeta de distribución local, manifiesto y restauración.

**Evidencia para cerrar:** Instalación limpia y prueba offline documentada con versión de Windows.

**Revisión antes de entregar — QA + integración:**
- [ ] Implementación: Crear paquete y manifiesto de versiones/hashes con diagnóstico.
- [ ] Casos adversos: Probar copia limpia, ruta con espacios, red ausente y asset alterado.
- [ ] Revisión final: Una persona distinta ejecuta normal/fallo siguiendo solo la guía.

## M5 — Validación y ajustes (8–9 nov.)

### F-17 · Matriz de fallos y métricas de aceptación

**Objetivo:** cerrar riesgos observables antes del pitch.
**Trabajo:** ejecutar casos de taladro incorrecto, valores divergentes, sensor ficticio ocupado, orden repetida, fallo de simulador, modo manual, ASR equivocado y pérdida de micrófono. Medir latencia y resultados del corpus. Priorizar y corregir fallos P0.
**Cierre:** matriz con esperado/observado, evidencia y estado de corrección; no quedan fallos que permitan completar una acción simulada tras un rechazo.

**Entregable verificable:** planning/RESULTADOS_VALIDACION.md con matriz esperado/observado, evidencia, defecto y resolución.

**Criterios de aceptación detallados:** Cubrir ID, kg, mezcla, zona ocupada, repetición, confirmación vencida, fallo/timeout, manual, ASR y micrófono; cero fallos P0 conocidos que avancen tras rechazo.

**Evidencia para cerrar:** Repetir casos corregidos; métricas con denominador y condición; revisión cruzada.

**Revisión antes de entregar — Producto + seguridad:**
- [ ] Implementación: Registrar esperado, observado, evidencia y severidad de cada fallo.
- [ ] Casos adversos: Incluir errores de voz, estado, modo, timeout y sensor ficticio.
- [ ] Revisión final: Repetir casos corregidos y revisar que ninguna acción avance tras rechazo.

### F-18 · Prueba de comprensión con usuarios del equipo

**Objetivo:** detectar confusión de interfaz sin fingir validación minera.
**Trabajo:** pedir a al menos dos personas que no implementaron la pantalla que ejecuten un ciclo y expliquen qué ocurrió en un rechazo. Registrar errores de interpretación y tiempo de tarea.
**Cierre:** los cambios relevantes se incorporan y el informe señala que los participantes no son operadores mineros.

**Entregable verificable:** Notas anonimizadas de dos participantes no autores de UI, tiempos y cambios.

**Criterios de aceptación detallados:** Ambos ejecutan ciclo, explican rechazo y demora; corregir confusión aceptado/completado; no presentar prueba como validación minera.

**Evidencia para cerrar:** Repetir paso confuso tras el cambio y conservar capturas antes/después.

**Revisión antes de entregar — Producto + interfaz:**
- [ ] Implementación: Preparar guion sin pistas y registrar tiempo/errores de dos participantes.
- [ ] Casos adversos: Observar confusión entre reconocido, aceptado y completado.
- [ ] Revisión final: Aplicar correcciones y repetir la tarea que produjo confusión.

### F-28 · Pruebas integradas y puerta de calidad en CI

**Objetivo:** Detectar regresiones del flujo completo en cada push.

**Trabajo:** Automatizar dos taladros, divergencia, zona ocupada, evento tardío, doble orden, modo y reinicio con BD temporal. Qt offscreen donde corresponda; audio real queda en ensayo manual.

**Cierre:** Suite pasa en CI Windows y local; una transición prohibida hace fallar test; rechazo nunca muta operación ni se completa sin evento.

**Entregable verificable:** Suite de integración, fixtures y workflow actualizado.

**Evidencia para cerrar:** Enlace a CI, reporte y control negativo documentado.

**Revisión antes de entregar — Seguridad + integración:**
- [ ] Implementación: Automatizar flujo de dos taladros y casos negativos con BD temporal.
- [ ] Casos adversos: Incluir carrera de órdenes, timeout, reinicio y evento ajeno.
- [ ] Revisión final: Adjuntar CI Windows y confirmar que transición prohibida hace fallar la suite.

## M6 — Entrega (9–10 nov.)

### F-19 · Guion, evidencia y pitch de 5 minutos

**Objetivo:** demostrar pertinencia, innovación, prototipo, viabilidad e impacto con evidencia.
**Trabajo:** preparar recorrido de caso normal + fallo, arquitectura, métricas, comparación con flujo manual hipotético y ruta de piloto con ORICA. Ensayar 5 minutos y preguntas sobre seguridad, conexión, operador y offline. Evitar estimar ahorro real sin medición de campo.
**Cierre:** presentación ensayada dentro del tiempo, guion de respaldo por teclado y capturas/video local por si falla el audio en sala.

**Entregable verificable:** Guion de 5 minutos, presentación, FAQ y evidencia local de respaldo.

**Criterios de aceptación detallados:** Ensayo cronometrado cubre problema, flujo, fallo, métricas, límites y piloto; respaldo por teclado reproduce mismas decisiones; no afirmar ahorro medido ni aprobación.

**Evidencia para cerrar:** Acta de ensayo y revisión de afirmaciones por un segundo integrante.

**Revisión antes de entregar — Producto + QA:**
- [ ] Implementación: Vincular cada afirmación del pitch con pantalla, prueba o fuente.
- [ ] Casos adversos: Ensayar fallo de micrófono y usar recorrido alternativo por teclado.
- [ ] Revisión final: Cronometrar cinco minutos y revisar que métricas y límites sean exactos.

### F-20 · Congelar versión y verificar entrega

**Objetivo:** presentar una versión estable y recuperable.
**Trabajo:** etiquetar versión, revisar instrucciones y datos ficticios, probar laptop/micrófono, guardar copia local y ejecutar la matriz crítica una última vez. Cambios posteriores solo para bloqueos reproducibles.
**Cierre:** carpeta de entrega, modelo de voz, guion y resultados se abren sin red; responsable de cada componente confirma su parte.

**Entregable verificable:** Tag/commit de entrega, checklist por rol, copia local y defectos conocidos.

**Criterios de aceptación detallados:** Caso normal y rechazo funcionan sin red en laptop; modelo y fixtures coinciden con paquete; cada componente tiene responsable; cambios posteriores solo por bloqueo reproducible.

**Evidencia para cerrar:** Ensayo final y comparación de manifiesto/hash con carpeta entregada.

**Revisión antes de entregar — QA + producto:**
- [ ] Implementación: Fijar commit, tag, hashes y lista de defectos residuales.
- [ ] Casos adversos: Ejecutar normal y rechazo tras desconectar red y reiniciar app.
- [ ] Revisión final: Otro integrante coteja paquete, manifiesto y evidencia antes de congelar.

### F-29 · Manifiesto de entrega y traspaso

**Objetivo:** Permitir a otra persona instalar, ejecutar, evaluar y continuar Faro sin explicación oral.

**Trabajo:** Reunir versión, requisitos, estructura, guía offline, diagnóstico, escenarios, métricas, límites, preguntas ORICA y ruta de piloto autorizado; no incluir audio ni material privado del briefing.

**Cierre:** Un integrante ajeno sigue guía y ejecuta normal/fallo; sin enlaces rotos ni afirmaciones de conexión real.

**Entregable verificable:** ENTREGA_FARO.md y manifiesto de archivos.

**Evidencia para cerrar:** Prueba de traspaso cronometrada y checklist de carpeta final.

**Revisión antes de entregar — Producto + QA:**
- [ ] Implementación: Ordenar guía, versión, escenarios, resultados, límites y preguntas a ORICA.
- [ ] Casos adversos: Abrir cada enlace/archivo del manifiesto en carpeta offline.
- [ ] Revisión final: Pedir traspaso a alguien ajeno y anotar pasos que requirieron ayuda.

## Regla para cerrar un issue

El responsable adjunta enlace a PR/commit y evidencia concreta: prueba ejecutada, captura, registro o archivo modificado; otro integrante revisa los casos de rechazo relevantes. Las reglas de este backlog son para un simulador ficticio, no constituyen aprobación de ORICA ni integran una MMU real. «Funciona en mi equipo» o una transcripción correcta aislada no bastan para cerrar un issue que autoriza cambios de estado.
