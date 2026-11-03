# Faro — backlog de issues para el Reto 3 ORICA

**Estado inicial al 2 de noviembre de 2026:** todos los issues están pendientes. `P0` bloquea la versión integrada; `P1` mejora la claridad o validación. Las personas del equipo pueden escribir su nombre junto al rol. El [plan y calendario](PLAN_FARO_ORICA.md) contienen las puertas de salida de cada hito.

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
| F-15 | M4 | P0 | Integración completa voz–reglas–simulador–UI | Integración | F-07, F-08, F-10, F-13 |
| F-16 | M4 | P0 | Arranque reproducible sin Internet | Integración | F-15 |
| F-17 | M5 | P0 | Matriz de fallos y métricas de aceptación | QA + todos | F-11, F-15, F-16 |
| F-18 | M5 | P1 | Prueba de comprensión con usuarios del equipo | Producto/interfaz | F-15 |
| F-19 | M6 | P0 | Guion, evidencia y pitch de 5 minutos | Producto + todos | F-17 |
| F-20 | M6 | P0 | Congelar versión y verificar entrega | Integración + todos | F-16, F-17, F-19 |

## M0 — Alcance y contrato (2 nov.)

### F-01 · Cerrar alcance y registrar decisiones

**Objetivo:** traducir las respuestas del briefing a un contrato de producto y separar hechos de propuestas.
**Trabajo:** definir operador, taladro, plan, acciones, estados, mensajes y alcance del simulador. Abrir una lista de preguntas para ORICA mediante el comité; registrar respuesta, fecha y efecto en el alcance.
**Cierre:** existe un diagrama de un ciclo por taladro, una lista de supuestos explícitos y un guion de caso normal y excepcional que el equipo puede explicar sin contradicciones.

### F-02 · Matriz de órdenes y condiciones de rechazo

**Objetivo:** que cada orden tenga una intención, precondiciones y salida definida.
**Trabajo:** construir tabla para `consultar taladro`, `extender/retraer brazo`, `extender/retraer manguera`, `preparar carga`, `pausar`, `consultar estado`, `cerrar taladro` y `siguiente taladro`. Marcar cuáles son solo simuladas, qué datos exigen y qué ocurre ante micrófono, estado o sensor ficticio adverso.
**Cierre:** toda orden tiene estados permitidos/prohibidos, mensaje de rechazo y evento de auditoría; ninguna frase desconocida se convierte en acción por similitud.

### F-03 · Malla y datos ficticios reproducibles

**Objetivo:** tener un escenario coherente antes de diseñar pantallas.
**Trabajo:** crear una malla local de al menos 3 taladros con ID, mezcla, cantidad prevista, método de entrega y estado. Incluir un taladro normal, uno con discrepancia y uno bloqueado. Identificar todos los datos como simulados.
**Cierre:** el mismo archivo o semilla genera el mismo recorrido y no contiene diseños ni cantidades operacionales de ORICA.

## M1 — Dominio y MMU simulada (3–5 nov.)

### F-04 · Motor de estados del ciclo por taladro

**Objetivo:** sustituir la revisión auxiliar ficticia actual.
**Trabajo:** implementar estados como `sin selección → taladro consultado → preparado → acción en curso → carguío simulado → cerrado → siguiente`, con transiciones explícitas y cancelación. Mantener el motor separado de Qt y del ASR.
**Cierre:** pruebas unitarias cubren un ciclo válido, órdenes fuera de orden, repetición y cambio de taladro durante una acción.

### F-05 · Adaptador de MMU simulada y eventos

**Objetivo:** probar la diferencia entre una orden aceptada y una acción concluida.
**Trabajo:** definir una interfaz interna para solicitar acciones y recibir `aceptada`, `en curso`, `completada`, `fallida` o `cancelada`. Implementar respuestas tardías y fallo inyectable; ninguna salida física o de red.
**Cierre:** la UI no puede mostrar «completado» antes del evento correspondiente y una acción fallida no cambia el estado final a éxito.

### F-06 · Excepciones de taladro, cantidad y mezcla

**Objetivo:** reflejar los desvíos de campo mencionados por ORICA sin inventar autorización.
**Trabajo:** detectar ID distinto, cantidad/mezcla divergente, taladro bloqueado o dato faltante. Abrir un estado de excepción; registrar causa y bloquear carguío simulado hasta que un flujo ficticio explícito lo resuelva.
**Cierre:** cada excepción se reproduce con un caso y queda claro en pantalla si se requiere revisión humana. El prototipo no trata un «sí» de voz como autorización industrial.

### F-07 · Sesión y modos voz/manual excluyentes

**Objetivo:** modelar al operador responsable y evitar órdenes simultáneas.
**Trabajo:** añadir identidad ficticia de sesión y modos `voz`, `manual` y `deshabilitado`. Al fallar el ASR, permitir detener la escucha y pasar explícitamente al modo manual simulado.
**Cierre:** los comandos hablados se rechazan en modo manual; no hay dos acciones activas; una transferencia queda registrada. La sesión no se presenta como biometría por voz.

### F-08 · Bitácora de decisiones y resultados

**Objetivo:** reconstruir qué se dijo, qué se decidió y qué sucedió.
**Trabajo:** ampliar SQLite para guardar hora, operador ficticio, fuente, transcripción, intención, taladro, estado anterior, decisión, motivo y evento final. Migrar la estructura existente o crear una nueva versión sin perder arranque.
**Cierre:** la secuencia de un caso exitoso y uno rechazado puede consultarse tras reiniciar; no se almacena audio crudo.

## M2 — Canal de voz local (3–6 nov.)

### F-09 · Vocabulario de Faro y análisis de números

**Objetivo:** tener órdenes cortas y pronunciables para el caso real.
**Trabajo:** fijar frases canónicas y variantes limitadas; reconocer IDs de taladro y kilos en palabras o cifras sin inferir valores ambiguos. Permitir `Oye Faro` como prefijo con escucha activa. Reservar una frase de activación continua para investigación posterior.
**Cierre:** tabla de al menos 20 frases positivas y 30 negativas; cada frase esperada tiene intención/argumentos inequívocos; valores dudosos se rechazan.

### F-10 · Conectar ASR local al nuevo dominio

**Objetivo:** reutilizar Vosk y el micrófono existentes para el flujo por taladro.
**Trabajo:** integrar transcripciones con el analizador de F-09 y el motor de F-04, mantener botón/F8 y selección de dispositivo. Mostrar error de micrófono y pérdida de escucha.
**Cierre:** un ciclo por taladro puede hacerse con voz en audio limpio sin Internet; comandos desconocidos no producen una acción.

### F-11 · Corpus y evaluación de voz

**Objetivo:** medir reconocimiento y falsas aceptaciones en condiciones identificadas.
**Trabajo:** ampliar el evaluador existente con al menos 2 personas del equipo, frases de comandos, nombres/IDs, números, conversaciones parecidas y ruido reproducido por separado. Reportar por caso transcripción, decisión y latencia.
**Cierre:** informe con denominadores, condiciones y errores; se distingue audio sintético de humano. Las metas de prototipo del plan se evalúan y cualquier incumplimiento queda documentado.

## M3 — Consola operacional (3–6 nov.)

### F-12 · Consola de operación por taladro

**Objetivo:** reemplazar la UI de temperatura/presión/batería por una pantalla útil para el caso.
**Trabajo:** mostrar malla ficticia, taladro activo, mezcla y kilos previstos, método de entrega, estado de brazo/manguera, modo de control y último comando. Mantener diseño formal y legible a distancia de laptop.
**Cierre:** una captura de pantalla permite identificar en pocos segundos taladro, plan, estado y si se trata de una simulación.

### F-13 · Estados de ejecución y alertas claras

**Objetivo:** impedir que el operador confunda una transcripción con una acción finalizada.
**Trabajo:** visualizar `escuchado`, `interpretado`, `validando`, `en curso`, `completado`, `rechazado` y `requiere revisión`, más motivo preciso. Evitar colores como única señal.
**Cierre:** casos de demora, rechazo y fallo del simulador se distinguen visualmente y aparecen en la bitácora.

### F-14 · Confirmaciones breves y ergonomía

**Objetivo:** dar retroalimentación útil sin saturar la cabina.
**Trabajo:** redactar mensajes cortos con ID de taladro y resultado. Evaluar TTS local únicamente para lectura de estado y confirmaciones; si suena confuso o retrasa el flujo, dejar respuesta visual. Revisar tamaños de fuente, contraste y uso con auricular.
**Cierre:** la prueba con miembros del equipo permite repetir correctamente qué acción se completó y cuál falló; TTS no se usa como prueba de seguridad.

## M4 — Integración y empaquetado (6–8 nov.)

### F-15 · Integración completa voz–reglas–simulador–UI

**Objetivo:** unir componentes con un solo flujo de eventos y sin atajos desde la UI al simulador.
**Trabajo:** conectar señales de voz, analizador, motor, adaptador y bitácora; evitar dobles órdenes por clic/voz simultáneos; incluir fallos inyectables para la demostración.
**Cierre:** guion de dos taladros consecutivos funciona por voz y teclado; el resultado visual coincide con el estado y la bitácora.

### F-16 · Arranque reproducible sin Internet

**Objetivo:** ejecutar Faro en la laptop disponible sin instalaciones de último momento.
**Trabajo:** fijar dependencias, verificar modelo Vosk local, carpeta de datos, elección de micrófono, script de inicio y recuperación ante micrófono ausente. Mantener Docker como entorno de pruebas sin interfaz y verificar CI en Windows. Documentar un procedimiento de instalación y uno de ejecución.
**Cierre:** desde una copia limpia preparada, el programa arranca, completa el guion y se reinicia sin red; no depende de nube ni de servicios externos.

## M5 — Validación y ajustes (8–9 nov.)

### F-17 · Matriz de fallos y métricas de aceptación

**Objetivo:** cerrar riesgos observables antes del pitch.
**Trabajo:** ejecutar casos de taladro incorrecto, valores divergentes, sensor ficticio ocupado, orden repetida, fallo de simulador, modo manual, ASR equivocado y pérdida de micrófono. Medir latencia y resultados del corpus. Priorizar y corregir fallos P0.
**Cierre:** matriz con esperado/observado, evidencia y estado de corrección; no quedan fallos que permitan completar una acción simulada tras un rechazo.

### F-18 · Prueba de comprensión con usuarios del equipo

**Objetivo:** detectar confusión de interfaz sin fingir validación minera.
**Trabajo:** pedir a al menos dos personas que no implementaron la pantalla que ejecuten un ciclo y expliquen qué ocurrió en un rechazo. Registrar errores de interpretación y tiempo de tarea.
**Cierre:** los cambios relevantes se incorporan y el informe señala que los participantes no son operadores mineros.

## M6 — Entrega (9–10 nov.)

### F-19 · Guion, evidencia y pitch de 5 minutos

**Objetivo:** demostrar pertinencia, innovación, prototipo, viabilidad e impacto con evidencia.
**Trabajo:** preparar recorrido de caso normal + fallo, arquitectura, métricas, comparación con flujo manual hipotético y ruta de piloto con ORICA. Ensayar 5 minutos y preguntas sobre seguridad, conexión, operador y offline. Evitar estimar ahorro real sin medición de campo.
**Cierre:** presentación ensayada dentro del tiempo, guion de respaldo por teclado y capturas/video local por si falla el audio en sala.

### F-20 · Congelar versión y verificar entrega

**Objetivo:** presentar una versión estable y recuperable.
**Trabajo:** etiquetar versión, revisar instrucciones y datos ficticios, probar laptop/micrófono, guardar copia local y ejecutar la matriz crítica una última vez. Cambios posteriores solo para bloqueos reproducibles.
**Cierre:** carpeta de entrega, modelo de voz, guion y resultados se abren sin red; responsable de cada componente confirma su parte.

## Regla para cerrar un issue

El responsable adjunta evidencia concreta: prueba ejecutada, captura, registro o archivo modificado; otro integrante revisa los casos de rechazo relevantes. «Funciona en mi equipo» o una transcripción correcta aislada no bastan para cerrar un issue que autoriza cambios de estado.
