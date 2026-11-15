# Faro — guion de presentación de 5 minutos

Versión de referencia: `d4dad23` · fecha de ensayo pendiente. El guion describe
un simulador local; no afirma conexión con maquinaria ORICA ni ahorros medidos.

## Guion cronometrado

| Tiempo | Mensaje | Evidencia que se muestra |
|---|---|---|
| 0:00–0:40 | Problema: durante el carguío el operador necesita consultar el taladro y mantener las manos en la tarea; una voz libre no debe ejecutar órdenes ambiguas. | Pantalla inicial y `planning/ALCANCE_Y_DECISIONES.md`. |
| 0:40–1:20 | Propuesta: Faro es una consola local, con vocabulario cerrado, reglas explícitas, sesión visible y controles físicos siempre prioritarios. | Arquitectura y etiqueta «simulación únicamente». |
| 1:20–2:40 | Flujo normal: seleccionar 101, consultar, preparar, declarar producto/masa, extender brazo con zona libre, completar carga, retraer y cerrar. | UI por taladro; estados reconocido/aceptado/en ejecución/completado. |
| 2:40–3:30 | Caso de seguridad: declarar producto o kg incorrectos y repetir una orden. Faro rechaza, no envía al simulador y registra el motivo. | Alerta visible y `RESULTADOS_VALIDACION.md` V-03/V-05. |
| 3:30–4:10 | Tecnología: Vosk local para ASR, parser cerrado, dominio determinista, adaptador MMU simulado y SQLite sin audio. | Diagrama de arquitectura y bitácora local. |
| 4:10–4:40 | Métricas: 190 pruebas locales, escenarios normal/fallo reproducibles offline y cero rechazos que avancen; CI Windows y corpus humano se reportan solo cuando exista evidencia. | Resultado de CI y matriz de validación. |
| 4:40–5:00 | Ruta de piloto: ORICA define equipo, órdenes y señales; luego se valida en entorno aislado antes de cualquier integración. | Preguntas abiertas y límites del prototipo. |

## Respaldo si falla el micrófono

1. Avisar: «La voz es opcional en esta prueba; las mismas reglas se ejecutan por
   teclado y no se oculta el fallo de captura».
2. Continuar con la entrada de texto usando el mismo flujo normal y el mismo
   caso de rechazo.
3. Mostrar `scripts/diagnose_offline.py --json` y la bitácora; no simular una
   transcripción que no ocurrió.

## Mapa de afirmaciones

| Afirmación | Tipo | Evidencia / límite |
|---|---|---|
| «Funciona sin Internet» | Hecho del prototipo | Vosk local, diagnóstico offline y CI; requiere modelo instalado. |
| «Una orden rechazada no avanza» | Hecho probado | Tests de dominio/controlador; solo simulador ficticio. |
| «Reduce accidentes o ahorra tiempo» | Hipótesis | Requiere medición de campo y aprobación de ORICA; no decirlo como resultado. |
| «Puede conectarse a la MMU» | Ruta futura | Falta contrato técnico, equipo y validación de ORICA; hoy no hay conectores. |
| «Reconoce al operador» | No implementado | La etiqueta de sesión no es biometría ni autenticación. |

## Preguntas previsibles y respuestas

**¿Es un Siri minero?** Es una interfaz de voz acotada para tareas autorizadas,
no un asistente conversacional libre. Una frase desconocida no genera una acción.

**¿Qué pasa si se equivoca el reconocimiento?** Se muestra la transcripción y
la decisión; si falta un dato, hay ambigüedad o no coincide el plan, se rechaza.

**¿Qué pasa si no hay red?** La transcripción Vosk es local. La instalación del
modelo se hace antes; durante la demostración no se requiere Internet.

**¿Puede mover una máquina real hoy?** No. El adaptador es un simulador en
memoria, sin sockets, PLC, radio ni salidas físicas.

**¿Cómo se integraría después?** ORICA debe proporcionar el equipo, estados,
interlocks, protocolo, autoridad del operador y entorno de pruebas; el adaptador
se validaría con esos contratos sin cambiar las reglas de seguridad.

## Acta de ensayo

| Fecha | Participantes | Duración | Micrófono | Caso normal | Caso de fallo | Revisión cruzada |
|---|---|---:|---|---|---|---|
| Pendiente | — | — | — | — | — | — |

