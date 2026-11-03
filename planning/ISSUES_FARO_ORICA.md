# Faro — backlog de issues para el Reto 3 ORICA

**Actualización al 3 de noviembre de 2026; entrega el 10 de noviembre.** El estado de cada issue se consulta en GitHub. `P0` bloquea la versión integrada; `P1` completa la calidad profesional de v1 y no se elimina por la fecha de entrega. Las personas del equipo pueden escribir su nombre junto al rol. El [plan y calendario](PLAN_FARO_ORICA.md) contienen las puertas de salida de cada hito.

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

### F-02 · Matriz de órdenes y condiciones de rechazo

**Objetivo:** que cada orden tenga una intención, precondiciones y salida definida.
**Trabajo:** construir tabla para `consultar taladro`, `extender/retraer brazo`, `extender/retraer manguera`, `preparar carga`, `pausar`, `consultar estado`, `cerrar taladro` y `siguiente taladro`. Marcar cuáles son solo simuladas, qué datos exigen y qué ocurre ante micrófono, estado o sensor ficticio adverso.
**Cierre:** toda orden tiene estados permitidos/prohibidos, mensaje de rechazo y evento de auditoría; ninguna frase desconocida se convierte en acción por similitud.

**Entregable verificable:** planning/CONTRATO_COMANDOS.md con intención, parámetros, fuente, estados, confirmación, rechazo y mensaje por orden.

**Criterios de aceptación detallados:** Cubrir consulta, selección, brazo, manguera, carga, pausa, cierre, siguiente y modo; número o unidad ausente, negación y frase desconocida no producen acción.

**Evidencia para cerrar:** Revisión conjunta de voz/lógica/UI; una prueba positiva y una negativa por intención.

### F-03 · Malla y datos ficticios reproducibles

**Objetivo:** tener un escenario coherente antes de diseñar pantallas.
**Trabajo:** crear una malla local de al menos 3 taladros con ID, mezcla, cantidad prevista, método de entrega y estado. Incluir un taladro normal, uno con discrepancia y uno bloqueado. Identificar todos los datos como simulados.
**Cierre:** el mismo archivo o semilla genera el mismo recorrido y no contiene diseños ni cantidades operacionales de ORICA.

**Entregable verificable:** Fixture JSON versionado de tres taladros y validador de esquema.

**Criterios de aceptación detallados:** IDs únicos, producto, kg y método explícitos; casos normal, divergente y bloqueado; archivo incompleto o duplicado falla antes de iniciar; datos rotulados ficticios.

**Evidencia para cerrar:** Tests de fixture válido, ID duplicado, campo ausente, kg inválidos y carga repetible.

### F-21 · Invariantes y alcance de seguridad del simulador

**Objetivo:** Escribir las reglas que nunca debe violar v1 en cualquier canal.

**Trabajo:** Definir una acción activa, rechazo sin mutación, taladro/kg/mezcla validados antes de carga, zona ficticia despejada antes de movimiento, exclusión voz/manual y completado solo tras evento final. Diferenciar pausa simulada de parada física de emergencia, que no se implementa.

**Cierre:** Cada invariante tiene prueba negativa y mensaje; controles ficticios y pendientes de ORICA se identifican como tales.

**Entregable verificable:** planning/INVARIANTES.md, tabla regla → prueba → resultado.

**Evidencia para cerrar:** Revisión de lógica/producto antes de cerrar motor, confirmación y timeouts.

## M1 — Dominio y MMU simulada (3–5 nov.)

### F-04 · Motor de estados del ciclo por taladro

**Objetivo:** sustituir la revisión auxiliar ficticia actual.
**Trabajo:** implementar estados como `sin selección → taladro consultado → preparado → acción en curso → carguío simulado → cerrado → siguiente`, con transiciones explícitas y cancelación. Mantener el motor separado de Qt y del ASR.
**Cierre:** pruebas unitarias cubren un ciclo válido, órdenes fuera de orden, repetición y cambio de taladro durante una acción.

**Entregable verificable:** Modelos tipados, tabla de transiciones y motor independiente de Qt y ASR.

**Criterios de aceptación detallados:** Ciclo por teclado de selección a cierre; fuera de secuencia, orden repetida y cambio de taladro durante acción no avanzan; decisión conserva estado antes/después e ID.

**Evidencia para cerrar:** Tests de camino feliz y cada transición prohibida; revisar que rechazo no muta estado operacional.

### F-05 · Adaptador de MMU simulada y eventos

**Objetivo:** probar la diferencia entre una orden aceptada y una acción concluida.
**Trabajo:** definir una interfaz interna para solicitar acciones y recibir `aceptada`, `en curso`, `completada`, `fallida` o `cancelada`. Implementar respuestas tardías y fallo inyectable; ninguna salida física o de red.
**Cierre:** la UI no puede mostrar «completado» antes del evento correspondiente y una acción fallida no cambia el estado final a éxito.

**Entregable verificable:** Contrato de adaptador y simulador con demora, fallo y eventos correlacionados por command_id.

**Criterios de aceptación detallados:** Enviar no equivale a completar; evento duplicado, tardío o de otro ID no cambia estado; no hay sockets, puertos industriales ni salidas físicas.

**Evidencia para cerrar:** Tests de aceptación, demora, finalización, fallo, evento duplicado e ID ajeno.

### F-06 · Excepciones de taladro, cantidad y mezcla

**Objetivo:** reflejar los desvíos de campo mencionados por ORICA sin inventar autorización.
**Trabajo:** detectar ID distinto, cantidad/mezcla divergente, taladro bloqueado o dato faltante. Abrir un estado de excepción; registrar causa y bloquear carguío simulado hasta que un flujo ficticio explícito lo resuelva.
**Cierre:** cada excepción se reproduce con un caso y queda claro en pantalla si se requiere revisión humana. El prototipo no trata un «sí» de voz como autorización industrial.

**Entregable verificable:** Estados y mensajes de excepción para ID, kg, mezcla, dato faltante, bloqueo y método.

**Criterios de aceptación detallados:** Ninguna discrepancia alcanza cargado; se ve plan y valor recibido; un sí de voz no autoriza cambio; corrección ficticia no reanuda orden antigua.

**Evidencia para cerrar:** Test por desviación y de recuperación; bitácora contiene causa y decisión.

### F-07 · Sesión y modos voz/manual excluyentes

**Objetivo:** modelar al operador responsable y evitar órdenes simultáneas.
**Trabajo:** añadir identidad ficticia de sesión y modos `voz`, `manual` y `deshabilitado`. Al fallar el ASR, permitir detener la escucha y pasar explícitamente al modo manual simulado.
**Cierre:** los comandos hablados se rechazan en modo manual; no hay dos acciones activas; una transferencia queda registrada. La sesión no se presenta como biometría por voz.

**Entregable verificable:** Modelo de sesión ficticia, estados voz/manual/deshabilitado y controles de cambio.

**Criterios de aceptación detallados:** Voz en manual se rechaza; detener escucha antes de transferencia; cambio durante acción no la completa; una sola acción activa; sesión no se presenta como biometría.

**Evidencia para cerrar:** Tests de transferencias y entrada simultánea voz/teclado; captura del modo visible.

### F-08 · Bitácora de decisiones y resultados

**Objetivo:** reconstruir qué se dijo, qué se decidió y qué sucedió.
**Trabajo:** ampliar SQLite para guardar hora, operador ficticio, fuente, transcripción, intención, taladro, estado anterior, decisión, motivo y evento final. Migrar la estructura existente o crear una nueva versión sin perder arranque.
**Cierre:** la secuencia de un caso exitoso y uno rechazado puede consultarse tras reiniciar; no se almacena audio crudo.

**Entregable verificable:** Esquema SQLite versionado, migración desde decisions actual y consulta por command_id.

**Criterios de aceptación detallados:** Persisten hora UTC, sesión, fuente, transcripción, intención, taladro, estados, decisión, motivo y eventos; no audio; reinicio reconstruye éxito y rechazo.

**Evidencia para cerrar:** Test con BD anterior temporal, reinicio y correlación de evento tardío.

### F-22 · Confirmación, pausa y cancelación simuladas

**Objetivo:** Evitar que una frase incompleta, caducada o repetida desencadene una acción.

**Trabajo:** Definir en el contrato qué movimiento/carga requiere confirmación; mostrar resumen de taladro, acción, producto y kg cuando aplique; ventana temporal; cancelar descarta; pausar interrumpe según estado. Es una regla de prototipo, no política de ORICA.

**Cierre:** Confirmación vencida, de otro taladro o con datos cambiados no ejecuta; repetición no duplica; cancelación queda auditada.

**Entregable verificable:** Estado pending_confirmation, temporizador y mensajes.

**Evidencia para cerrar:** Tests de confirmar, rechazar, vencer, repetir y cambiar contexto.

### F-23 · Timeout, eventos tardíos y recuperación

**Objetivo:** Mantener estado conservador si el simulador no responde o la app se interrumpe.

**Trabajo:** Fijar timeout configurable de prototipo; una solicitud sin respuesta pasa a desconocido/requiere revisión y bloquea órdenes dependientes. Al reiniciar, no reenviar automáticamente. Correlacionar eventos tardíos y duplicados por ID.

**Cierre:** La demora no aparece completada; reinicio no infiere éxito; evento tardío no completa otra orden; la recuperación manual simulada es visible.

**Entregable verificable:** Política de timeout/reinicio y código con reloj inyectable.

**Evidencia para cerrar:** Tests deterministas de timeout, reinicio, duplicado y evento tardío.

### F-24 · Escenarios reproducibles e inyección de fallos

**Objetivo:** Repetir guion y fallos sin modificar el código.

**Trabajo:** Versionar escenarios de zona ficticia ocupada, taladro bloqueado, fallo de brazo/manguera, demora y rechazo del adaptador; selector rotulado simulación; reinicio de semilla.

**Cierre:** Cada escenario produce igual resultado dos veces y deja eventos auditables; el modo normal no hereda fallos anteriores.

**Entregable verificable:** Fixtures, cargador y guía de reproducción.

**Evidencia para cerrar:** Tests por fixture y ensayo manual de reinicio.

## M2 — Canal de voz local (3–6 nov.)

### F-09 · Vocabulario de Faro y análisis de números

**Objetivo:** tener órdenes cortas y pronunciables para el caso real.
**Trabajo:** fijar frases canónicas y variantes limitadas; reconocer IDs de taladro y kilos en palabras o cifras sin inferir valores ambiguos. Permitir `Oye Faro` como prefijo con escucha activa. Reservar una frase de activación continua para investigación posterior.
**Cierre:** tabla de al menos 20 frases positivas y 30 negativas; cada frase esperada tiene intención/argumentos inequívocos; valores dudosos se rechazan.

**Entregable verificable:** Parser determinista y tabla de al menos 20 frases positivas y 30 negativas.

**Criterios de aceptación detallados:** Cada positivo da intención y argumentos exactos; negación, dos acciones, valor dudoso, unidad faltante o frase ajena se rechazan; Oye Faro solo es prefijo con escucha activa.

**Evidencia para cerrar:** Tests parametrizados de acentos, cifras/palabras, IDs, kg, unidades y negativos.

### F-10 · Conectar ASR local al nuevo dominio

**Objetivo:** reutilizar Vosk y el micrófono existentes para el flujo por taladro.
**Trabajo:** integrar transcripciones con el analizador de F-09 y el motor de F-04, mantener botón/F8 y selección de dispositivo. Mostrar error de micrófono y pérdida de escucha.
**Cierre:** un ciclo por taladro puede hacerse con voz en audio limpio sin Internet; comandos desconocidos no producen una acción.

**Entregable verificable:** Integración Vosk local → parser → motor y estados visibles de escucha.

**Criterios de aceptación detallados:** Completar ciclo limpio sin Internet; resultado parcial/final no duplica acción; frase desconocida no cambia estado; hilo de UI responde durante reconocimiento.

**Evidencia para cerrar:** Tests con transcripciones y ensayo documentado con micrófono, dispositivo y entorno.

### F-11 · Corpus y evaluación de voz

**Objetivo:** medir reconocimiento y falsas aceptaciones en condiciones identificadas.
**Trabajo:** ampliar el evaluador existente con al menos 2 personas del equipo, frases de comandos, nombres/IDs, números, conversaciones parecidas y ruido reproducido por separado. Reportar por caso transcripción, decisión y latencia.
**Cierre:** informe con denominadores, condiciones y errores; se distingue audio sintético de humano. Las metas de prototipo del plan se evalúan y cualquier incumplimiento queda documentado.

**Entregable verificable:** Corpus local consentido, manifiesto de casos y reporte de métricas por condición.

**Criterios de aceptación detallados:** Al menos dos voces humanas; separar audio limpio, ruido reproducido y sintético; reportar denominadores, falsas aceptaciones, p50/p95 y cada meta no lograda.

**Evidencia para cerrar:** Repetir evaluación con mismo corpus; revisar manualmente falsos positivos; no publicar WAV privados.

### F-25 · Fallos de audio y estado real de escucha

**Objetivo:** Evitar que la UI afirme escuchar tras fallo de captura.

**Trabajo:** Detectar modelo ausente, dispositivo inválido, desconexión, permisos y fallo del hilo; cerrar recursos, bloquear voz y ofrecer reconexión explícita. Entrada escrita sigue disponible.

**Cierre:** Cada fallo muestra no disponible/detenido; F8 refleja estado real; reintento no crea dos hilos ni decisiones.

**Entregable verificable:** Estados de captura, mensajes y ruta de recuperación.

**Evidencia para cerrar:** Tests con dispositivo simulado y ensayo de desconexión de micrófono.

## M3 — Consola operacional (3–6 nov.)

### F-12 · Consola de operación por taladro

**Objetivo:** reemplazar la UI de temperatura/presión/batería por una pantalla útil para el caso.
**Trabajo:** mostrar malla ficticia, taladro activo, mezcla y kilos previstos, método de entrega, estado de brazo/manguera, modo de control y último comando. Mantener diseño formal y legible a distancia de laptop.
**Cierre:** una captura de pantalla permite identificar en pocos segundos taladro, plan, estado y si se trata de una simulación.

**Entregable verificable:** Consola Qt por taladro con malla, plan, método, brazo/manguera, modo, escucha y último resultado.

**Criterios de aceptación detallados:** Una captura identifica taladro, plan, estado y simulación; dos taladros se recorren sin cambiar de ventana; UI solo emite intenciones.

**Evidencia para cerrar:** Prueba Qt offscreen y recorrido manual de tres fixtures con captura.

### F-13 · Estados de ejecución y alertas claras

**Objetivo:** impedir que el operador confunda una transcripción con una acción finalizada.
**Trabajo:** visualizar `escuchado`, `interpretado`, `validando`, `en curso`, `completado`, `rechazado` y `requiere revisión`, más motivo preciso. Evitar colores como única señal.
**Cierre:** casos de demora, rechazo y fallo del simulador se distinguen visualmente y aparecen en la bitácora.

**Entregable verificable:** Tabla evento → mensaje y componentes para escuchado, interpretado, pendiente, en curso, completado, rechazado, fallido y revisión.

**Criterios de aceptación detallados:** Demora permanece en curso; fallo y rechazo se distinguen sin depender solo del color; evento de otro ID no cambia la vista; bitácora y pantalla concuerdan.

**Evidencia para cerrar:** Pruebas UI de demora, fallo, rechazo, excepción y correlación.

### F-14 · Confirmaciones breves y ergonomía

**Objetivo:** dar retroalimentación útil sin saturar la cabina.
**Trabajo:** redactar mensajes cortos con ID de taladro y resultado. Evaluar TTS local únicamente para lectura de estado y confirmaciones; si suena confuso o retrasa el flujo, dejar respuesta visual. Revisar tamaños de fuente, contraste y uso con auricular.
**Cierre:** la prueba con miembros del equipo permite repetir correctamente qué acción se completó y cuál falló; TTS no se usa como prueba de seguridad.

**Entregable verificable:** Catálogo de mensajes breves con ID/acción/resultado y checklist de ergonomía.

**Criterios de aceptación detallados:** Dos usuarios pueden repetir qué terminó y qué se rechazó; resultado sigue visible si TTS falla; teclado, contraste y tamaño legibles en laptop/auricular.

**Evidencia para cerrar:** Ensayo de comprensión y captura de estados; registrar decisión de incluir o no TTS local.

## M4 — Integración y empaquetado (6–8 nov.)

### F-15 · Integración completa voz–reglas–simulador–UI

**Objetivo:** unir componentes con un solo flujo de eventos y sin atajos desde la UI al simulador.
**Trabajo:** conectar señales de voz, analizador, motor, adaptador y bitácora; evitar dobles órdenes por clic/voz simultáneos; incluir fallos inyectables para la demostración.
**Cierre:** guion de dos taladros consecutivos funciona por voz y teclado; el resultado visual coincide con el estado y la bitácora.

**Entregable verificable:** Composición ASR-parser-motor-adaptador-auditoría-UI y guion técnico.

**Criterios de aceptación detallados:** Dos taladros consecutivos por voz o texto; rechazo no llama al adaptador; clic/voz simultáneos no duplican comando; SQLite, UI y motor coinciden.

**Evidencia para cerrar:** Tests de integración sin hardware y recorrido manual en laptop.

### F-16 · Arranque reproducible sin Internet

**Objetivo:** ejecutar Faro en la laptop disponible sin instalaciones de último momento.
**Trabajo:** fijar dependencias, verificar modelo Vosk local, carpeta de datos, elección de micrófono, script de inicio y recuperación ante micrófono ausente. Mantener Docker como entorno de pruebas sin interfaz y verificar CI en Windows. Documentar un procedimiento de instalación y uno de ejecución.
**Cierre:** desde una copia limpia preparada, el programa arranca, completa el guion y se reinicia sin red; no depende de nube ni de servicios externos.

**Entregable verificable:** Guía de instalación y arranque, versiones fijadas, diagnóstico local y checklist offline.

**Criterios de aceptación detallados:** Copia limpia preparada inicia, completa guion y reinicia sin red; falta de modelo/malla/micrófono da mensaje útil; Docker solo prueba código sin GUI.

**Evidencia para cerrar:** CI Windows, ensayo con red desactivada y registro de versión de Python/Windows.

### F-26 · Privacidad de transcripciones y exportación de evidencia

**Objetivo:** Conservar trazabilidad sin divulgar voces ni datos privados de ensayo.

**Trabajo:** Definir ubicación, acceso y limpieza de SQLite; exportar reporte ficticio de decisiones/eventos sin audio; revisar .gitignore y paquete para excluir BD, WAV, briefing y secretos; documentar consentimiento del corpus.

**Cierre:** Evidencia presentable sin audio humano ni datos personales; carpeta de entrega no contiene ensayos no autorizados.

**Entregable verificable:** Política breve, comando de exportación/limpieza y reporte ficticio.

**Evidencia para cerrar:** Pruebas de exportación/borrado y revisión de archivos rastreados y empaquetados.

### F-27 · Paquete offline verificable para Windows

**Objetivo:** Entregar carpeta ejecutable comprobable en la laptop prevista.

**Trabajo:** Empaquetar app, dependencias, modelo local permitido, malla ficticia, guía y diagnóstico. Crear manifiesto de versiones y hashes; probar rutas con espacios; no presuponer administrador o instalador.

**Cierre:** Otro integrante abre carpeta sin red y recorre caso normal/fallo; falta o hash incorrecto de asset esencial se detecta al inicio.

**Entregable verificable:** Carpeta de distribución local, manifiesto y restauración.

**Evidencia para cerrar:** Instalación limpia y prueba offline documentada con versión de Windows.

## M5 — Validación y ajustes (8–9 nov.)

### F-17 · Matriz de fallos y métricas de aceptación

**Objetivo:** cerrar riesgos observables antes del pitch.
**Trabajo:** ejecutar casos de taladro incorrecto, valores divergentes, sensor ficticio ocupado, orden repetida, fallo de simulador, modo manual, ASR equivocado y pérdida de micrófono. Medir latencia y resultados del corpus. Priorizar y corregir fallos P0.
**Cierre:** matriz con esperado/observado, evidencia y estado de corrección; no quedan fallos que permitan completar una acción simulada tras un rechazo.

**Entregable verificable:** planning/RESULTADOS_VALIDACION.md con matriz esperado/observado, evidencia, defecto y resolución.

**Criterios de aceptación detallados:** Cubrir ID, kg, mezcla, zona ocupada, repetición, confirmación vencida, fallo/timeout, manual, ASR y micrófono; cero fallos P0 conocidos que avancen tras rechazo.

**Evidencia para cerrar:** Repetir casos corregidos; métricas con denominador y condición; revisión cruzada.

### F-18 · Prueba de comprensión con usuarios del equipo

**Objetivo:** detectar confusión de interfaz sin fingir validación minera.
**Trabajo:** pedir a al menos dos personas que no implementaron la pantalla que ejecuten un ciclo y expliquen qué ocurrió en un rechazo. Registrar errores de interpretación y tiempo de tarea.
**Cierre:** los cambios relevantes se incorporan y el informe señala que los participantes no son operadores mineros.

**Entregable verificable:** Notas anonimizadas de dos participantes no autores de UI, tiempos y cambios.

**Criterios de aceptación detallados:** Ambos ejecutan ciclo, explican rechazo y demora; corregir confusión aceptado/completado; no presentar prueba como validación minera.

**Evidencia para cerrar:** Repetir paso confuso tras el cambio y conservar capturas antes/después.

### F-28 · Pruebas integradas y puerta de calidad en CI

**Objetivo:** Detectar regresiones del flujo completo en cada push.

**Trabajo:** Automatizar dos taladros, divergencia, zona ocupada, evento tardío, doble orden, modo y reinicio con BD temporal. Qt offscreen donde corresponda; audio real queda en ensayo manual.

**Cierre:** Suite pasa en CI Windows y local; una transición prohibida hace fallar test; rechazo nunca muta operación ni se completa sin evento.

**Entregable verificable:** Suite de integración, fixtures y workflow actualizado.

**Evidencia para cerrar:** Enlace a CI, reporte y control negativo documentado.

## M6 — Entrega (9–10 nov.)

### F-19 · Guion, evidencia y pitch de 5 minutos

**Objetivo:** demostrar pertinencia, innovación, prototipo, viabilidad e impacto con evidencia.
**Trabajo:** preparar recorrido de caso normal + fallo, arquitectura, métricas, comparación con flujo manual hipotético y ruta de piloto con ORICA. Ensayar 5 minutos y preguntas sobre seguridad, conexión, operador y offline. Evitar estimar ahorro real sin medición de campo.
**Cierre:** presentación ensayada dentro del tiempo, guion de respaldo por teclado y capturas/video local por si falla el audio en sala.

**Entregable verificable:** Guion de 5 minutos, presentación, FAQ y evidencia local de respaldo.

**Criterios de aceptación detallados:** Ensayo cronometrado cubre problema, flujo, fallo, métricas, límites y piloto; respaldo por teclado reproduce mismas decisiones; no afirmar ahorro medido ni aprobación.

**Evidencia para cerrar:** Acta de ensayo y revisión de afirmaciones por un segundo integrante.

### F-20 · Congelar versión y verificar entrega

**Objetivo:** presentar una versión estable y recuperable.
**Trabajo:** etiquetar versión, revisar instrucciones y datos ficticios, probar laptop/micrófono, guardar copia local y ejecutar la matriz crítica una última vez. Cambios posteriores solo para bloqueos reproducibles.
**Cierre:** carpeta de entrega, modelo de voz, guion y resultados se abren sin red; responsable de cada componente confirma su parte.

**Entregable verificable:** Tag/commit de entrega, checklist por rol, copia local y defectos conocidos.

**Criterios de aceptación detallados:** Caso normal y rechazo funcionan sin red en laptop; modelo y fixtures coinciden con paquete; cada componente tiene responsable; cambios posteriores solo por bloqueo reproducible.

**Evidencia para cerrar:** Ensayo final y comparación de manifiesto/hash con carpeta entregada.

### F-29 · Manifiesto de entrega y traspaso

**Objetivo:** Permitir a otra persona instalar, ejecutar, evaluar y continuar Faro sin explicación oral.

**Trabajo:** Reunir versión, requisitos, estructura, guía offline, diagnóstico, escenarios, métricas, límites, preguntas ORICA y ruta de piloto autorizado; no incluir audio ni material privado del briefing.

**Cierre:** Un integrante ajeno sigue guía y ejecuta normal/fallo; sin enlaces rotos ni afirmaciones de conexión real.

**Entregable verificable:** ENTREGA_FARO.md y manifiesto de archivos.

**Evidencia para cerrar:** Prueba de traspaso cronometrada y checklist de carpeta final.

## Regla para cerrar un issue

El responsable adjunta enlace a PR/commit y evidencia concreta: prueba ejecutada, captura, registro o archivo modificado; otro integrante revisa los casos de rechazo relevantes. Las reglas de este backlog son para un simulador ficticio, no constituyen aprobación de ORICA ni integran una MMU real. «Funciona en mi equipo» o una transcripción correcta aislada no bastan para cerrar un issue que autoriza cambios de estado.
