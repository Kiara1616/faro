# Faro — plan de integración del reto ORICA

**Versión:** 1.1 · **Fecha de planificación:** 2 de noviembre de 2026 · **Entrega del proyecto fijada por el equipo:** 10 de noviembre de 2026
**Producto:** Faro, presentado inicialmente como SafeFlow AI.
**Fuente del alcance:** [análisis del briefing](../Analisis_briefing_Faro_ORICA_2026-10-28.md). Las respuestas del representante describen el trabajo de carguío por taladro y orientan el prototipo; no constituyen permiso para conectar maquinaria.

## Objetivo y resultado esperado

Entregar una aplicación de escritorio en español que permita al operador **consultar y controlar por voz un ciclo de carguío por taladro en una MMU simulada**, sin Internet durante la ejecución. Debe exhibir la secuencia completa: seleccionar taladro, consultar plan, preparar el método de entrega, simular movimiento de brazo o manguera, validar mezcla y cantidad, simular carguío, comprobar cierre y pasar al siguiente taladro. Debe demostrar rechazo seguro ante órdenes incorrectas o incompletas y registrar cada decisión.

El prototipo **no actuará sobre una MMU, PLC, LOADPlus o ProBlast real**. La conexión real es una fase posterior condicionada a documentación, permisos, acceso a un entorno de prueba y revisión de seguridad de ORICA.

### Objetivos medibles de v1

| ID | Objetivo | Evidencia de cumplimiento |
| --- | --- | --- |
| O1 | Representar el flujo real señalado en el briefing. | Una malla ficticia con al menos 3 taladros y un recorrido completo por taladro, desde consulta hasta cierre. |
| O2 | Mantener decisiones independientes del reconocimiento de voz. | Voz y teclado pasan por el mismo motor de reglas; ninguna transcripción acciona directamente el simulador. |
| O3 | Rechazar órdenes ambiguas o fuera de contexto. | Pruebas para ID erróneo, kilos o mezcla distintos del plan, zona ficticia ocupada, operación ya activa y orden repetida. |
| O4 | Diferenciar reconocer, autorizar, iniciar y terminar una acción. | La interfaz y la bitácora muestran cada estado; «completado» aparece solo después de la respuesta del simulador. |
| O5 | Permitir un retorno controlado a operación manual simulada. | Modos voz/manual excluyentes y transferencia tras fallo o desactivación explícita. |
| O6 | Demostrar funcionamiento local y medible. | Ensayo sin red, corpus de audio etiquetado, reporte de latencia y falsas aceptaciones en las condiciones probadas. |
| O7 | Comunicar honestamente el valor y los límites. | Pitch de 5 minutos y respuestas a preguntas: alcance, arquitectura, fallos, métricas y ruta de integración real. |

## Alcance funcional congelado para v1

**Incluido:** operador ficticio en sesión; plan de malla de prueba; consulta de taladro; comandos cerrados de brazo/manguera; cantidad y mezcla contrastadas con el plan; carguío y pausa **simulados**; avance al siguiente taladro; alertas; bitácora; modo manual simulado; reconocimiento local activado con botón/F8; «Oye Faro» como prefijo opcional con la escucha activa; respuesta visible y, si pasa las pruebas, voz local breve.

**Fuera de v1:** conexión a maquinaria, PLC o sensores reales; envío por LoRa; autenticación biométrica por voz; modificación automática de un plan real; aceptación libre de frases mediante LLM; prometer que «Oye Faro» despierta el micrófono continuamente; afirmar aprobación o nivel de seguridad industrial.

**Decisión de diseño:** el simulador utilizará un contrato de eventos (`comando → validación → solicitud → aceptación/rechazo → fin/fallo`). Así se podrá cambiar por un adaptador de pruebas futuro sin reescribir la UI ni el motor de reglas, pero el adaptador real no se implementará sin información técnica y autorización.

**Tecnología elegida:** Python 3.12 para dominio e integración, PySide6 para consola, Vosk y sounddevice para voz local, JSON para la malla ficticia, SQLite para auditoría y pytest para verificación. [La arquitectura detallada](ARQUITECTURA_FARO.md) define módulos y contratos. Docker se incorpora para pruebas sin interfaz; la demostración con micrófono se ejecuta de forma nativa en Windows. Go se evalúa solo si una integración futura exige una pasarela separada y se dispone de especificaciones; añadirlo ahora dividiría la lógica sin un beneficio demostrado.

## Hitos y puertas de salida

| Hito | Fechas objetivo | Resultado verificable | Issues |
| --- | --- | --- | --- |
| **M0 — Alcance y contrato** | 2 nov. | Flujo, estados, vocabulario, datos ficticios y supuestos aprobados internamente; preguntas enviables al comité. | F-01 a F-03 |
| **M1 — Dominio y MMU simulada** | 3–5 nov. | Ciclo completo por taladro con transiciones, excepciones, eventos y auditoría probados por teclado. | F-04 a F-08 |
| **M2 — Canal de voz local** | 3–6 nov. | Comandos del dominio nuevo reconocidos localmente y evaluados con audio etiquetado; invocación opcional después de activar escucha. | F-09 a F-11 |
| **M3 — Consola operacional** | 3–6 nov. | Interfaz sobria que muestra plan, estado, modo, progreso, alertas y confirmación de resultado. | F-12 a F-14 |
| **M4 — Integración y empaquetado** | 6–8 nov. | Un solo flujo de extremo a extremo en laptop y arranque sin red. | F-15 a F-16 |
| **M5 — Validación y ajustes** | 8–9 nov. | Matriz de fallos ejecutada, métricas reportadas y problemas graves resueltos. | F-17 a F-18 |
| **M6 — Entrega** | 9–10 nov. | Versión congelada, guion y pitch ensayados; carpeta de entrega reproducible. | F-19 a F-20 |

Las fechas son objetivos internos para entregar **todo el alcance de v1 el 10 de noviembre**. M1, M2 y M3 avanzan en paralelo a partir del contrato de M0; se integran por interfaces pactadas desde el 3 de noviembre, sin esperar a que cada componente esté terminado. M4 depende de sus contratos y de un recorrido funcional; M5 y M6 pueden preparar pruebas y presentación en paralelo. Ningún hito depende de obtener un PLC o un camión. Este calendario requiere trabajo simultáneo de los cuatro frentes y revisión diaria de bloqueos; no equivale a garantizar que todas las métricas se alcanzarán.

### Punto de control diario

| Fecha | Evidencia mínima al cierre del día |
| --- | --- |
| **2 nov.** | Contrato de comandos/estados, datos ficticios, responsables y arquitectura aprobados por el equipo. |
| **3 nov.** | Esqueleto del nuevo motor, vocabulario y boceto de la consola conectados a las mismas estructuras de datos. |
| **4 nov.** | Recorrido por teclado de un taladro; primer comando de voz del dominio nuevo; plan visible. |
| **5 nov.** | Dos taladros, excepciones y eventos del simulador; bitácora ampliada. |
| **6 nov.** | Voz, motor y consola recorren el flujo completo; modos excluyentes y alertas visibles. |
| **7 nov.** | Integración estable, evaluador de voz, inicio offline y primer ensayo de fallos. |
| **8 nov.** | Matriz de fallos ejecutada y correcciones de errores que cambian indebidamente el estado. |
| **9 nov.** | Métricas, prueba de comprensión, guion y pitch ensayados; versión candidata. |
| **10 nov.** | Prueba final sin red en la laptop, versión congelada y entrega. |

## Asignación sugerida para un equipo de software

| Responsabilidad | Trabajo principal | Revisión cruzada |
| --- | --- | --- |
| Responsable de producto/integración | F-01, F-03, F-15, F-19, F-20; contacto con comité. | Verifica que cada pantalla y frase corresponda al flujo del briefing. |
| Lógica y simulación | F-04 a F-08. | Revisa transiciones, rechazos y trazabilidad con el responsable de voz. |
| Voz y evaluación | F-09 a F-11 y apoyo en F-17. | Revisa falsos positivos y degradación con el responsable de lógica. |
| Interfaz y experiencia | F-12 a F-14 y apoyo en F-18. | Revisa legibilidad y claridad de estados con integración. |

Si son menos de cuatro personas, agrupar producto con interfaz y lógica con integración. Dado que el equipo no tiene un especialista de minería, **el flujo es una hipótesis informada por el briefing** hasta recibir observación o confirmación de ORICA. La revisión industrial futura debe hacerla personal competente de ORICA; no se sustituye con una revisión de software.

## Orden de construcción

1. Sustituir el modelo de «revisión auxiliar» por `malla`, `taladro`, `producto`, `kg previstos`, `modo de entrega`, `estado de brazo/manguera` y `estado de carguío`.
2. Fijar la tabla de comandos e interbloqueos ficticios en un documento antes de editar código. Las acciones sobre brazo/manguera se aceptan solo en estados válidos; cantidad/mezcla se comparan con el plan.
3. Construir y probar el motor y el simulador por teclado. El adaptador simulado emite confirmación tardía y fallos para impedir que la UI confunda recepción con ejecución.
4. Conectar Vosk local al nuevo vocabulario. Mantener botón/F8 para activar escucha. «Oye Faro» solo precede un comando cuando el micrófono ya está activo.
5. Rediseñar la consola para una operación por taladro: identificación visible, plan, estado actual, modo, orden escuchada, resultado y registro.
6. Ejecutar ensayos adversos, grabar métricas y preparar el pitch con lo que realmente funciona.

## Criterios de aceptación de la versión integrada

- Un evaluador puede completar **dos taladros ficticios consecutivos** con órdenes habladas o escritas, y ver el estado de cada uno.
- Una orden ambigua, de taladro equivocado o de cantidad/mezcla divergente **no inicia** el carguío simulado.
- El simulador permite provocar una zona ficticia ocupada, fallo de movimiento y fallo de voz. Cada caso deja un rechazo o interrupción visible y auditada.
- Una orden reconocida pero aún en progreso nunca aparece como «completada».
- Se puede cambiar al modo manual simulado de forma explícita; no se aceptan órdenes de voz mientras está activo el manual.
- El paquete arranca y completa el guion **sin conexión a Internet** en la laptop de presentación.
- Se reportan, con denominador y condiciones de prueba, tasa de reconocimiento correcto, falsas aceptaciones y latencia. Los objetivos internos iniciales son ≥90 % de comandos correctos en audio limpio, 0 falsas aceptaciones en al menos 30 casos negativos definidos y latencia p95 ≤2 s en la laptop de la demo. Estos umbrales son **metas de prototipo**, no criterios de seguridad industrial; si no se alcanzan, se informa el resultado y se restringe el vocabulario.

## Decisiones pendientes de ORICA y plan de contingencia

Enviar por el comité organizador hasta el 3 de noviembre: (a) acción que prefieren priorizar; (b) secuencia observada o grabación de pantalla sin datos sensibles; (c) lista de órdenes prohibidas y reglas de confirmación/supervisión; (d) modelo concreto de MMU y documentación de interfaz de pruebas; (e) modalidad de identificación del operador y material de audio autorizado. El canal por comité fue indicado en el briefing (20:22–20:49).

Si no llega respuesta, continuar con **malla y sensores ficticios**, etiquetados como tales. No ajustar el prototipo a un protocolo inferido de una ficha comercial ni representar las reglas propuestas como políticas oficiales de ORICA. Las respuestas posteriores se incorporan mediante el registro de decisiones de F-01, sin romper la fecha de entrega.

## Riesgos que controlan el alcance

| Riesgo | Mitigación verificable |
| --- | --- |
| Reconocimiento erróneo de kilos o mezcla | Gramática cerrada, lectura de vuelta del valor, comparación con el plan y bloqueo ante discrepancia. |
| Activación por conversación ajena | Escucha explícita; prefijo opcional no se considera autenticación; corpus de frases negativas. |
| Movimiento con persona próxima | Interbloqueo ficticio y escenario de rechazo. Un sensor real exigiría interfaz y validación de ORICA. |
| Falta de información de PLC | Adaptador simulado; interfaz interna documentada; ninguna promesa de compatibilidad. |
| Equipo pequeño y tiempo corto | Trabajo paralelo desde el 3 de noviembre, contrato estable entre módulos, integración diaria y revisión de bloqueos. TTS y wake word continuo siguen fuera del alcance definido de v1; no se elimina ninguna función incluida. |
| Métricas infladas por audio sintético | Separar pruebas sintéticas, voces reales y ruido reproducido; informar cada condición. |

## Backlog operativo

Los issues detallados están en [ISSUES_FARO_ORICA.md](ISSUES_FARO_ORICA.md). Cada uno tiene responsable por rol, dependencia y una condición clara para cerrarlo. El repositorio aún no tiene remoto de GitHub; estos IDs son el registro local listo para pasar a un gestor cuando el equipo configure uno.
