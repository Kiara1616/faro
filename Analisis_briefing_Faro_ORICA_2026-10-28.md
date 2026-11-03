# Faro — análisis del briefing técnico de ORICA

**Fuente principal:** grabación «ORICA - BRIEFING TÉCNICO - 2026_10_28 16_46 GMT-05_00 - Recording.mp4», 35:09. Las marcas de tiempo son posiciones aproximadas dentro del archivo. Se revisaron tanto las preguntas del equipo presentado como SafeFlow AI (ahora Faro) como las de otros participantes. La transcripción automática se contrastó en los pasajes decisivos; los nombres de productos y equipos se cotejaron con fichas públicas de los fabricantes. Este documento interpreta el briefing para orientar un prototipo, no certifica una solución industrial.

## 1. Qué problema concretó ORICA

El representante describió el **carguío de explosivo por taladro desde una unidad móvil de fabricación (MMU)**. El operador ubica la unidad junto al taladro, identifica el taladro y consulta un diseño de malla que ya asigna producto y cantidad. En la pantalla del sistema introduce o confirma el tipo de mezcla y los kilogramos; acciona el brazo de descarga o la manguera según la forma de entrega. El sistema carga la cantidad programada y luego retrae el elemento para pasar al siguiente taladro. **Video: 03:00–04:10 y 14:00–14:17.**

El operador puede encontrar un taladro tapado, más corto o más largo que lo diseñado y ajustar datos en campo. Eso obliga a tratar las excepciones como parte central del flujo. **Video: 06:15–06:48.** El representante dijo que la empresa esperaría a largo plazo más control por voz, pero aceptó como primera etapa funciones simples como extender/retraer brazo o manguera y expresó interés en dictar cantidad y mezcla. Esto es una orientación de alcance, no autorización técnica para conectar el prototipo al equipo. **Video: 01:47–02:13 y 09:15–10:00.**

**Implicación para Faro:** la actual revisión ficticia de temperatura, presión y batería sirve para probar la arquitectura, pero ya no representa el trabajo pedido. Hay que convertirla en un **simulador de operación por taladro**, con una consola formal en cabina, voz local y reglas explícitas.

## 2. Respuestas de ORICA que afectan el diseño

| Tema y tiempo | Respuesta del representante | Decisión para el prototipo |
| --- | --- | --- |
| Plan de carguío, 13:50–14:17 | El diseño previo indica cantidad y tipo de mezcla por taladro. | Precargar una malla **ficticia** y mostrar ID, producto y cantidad objetivo. El dictado debe contrastarse con ese plan. |
| Valores fuera de plan, 14:34–15:40 y 22:29–23:00 | Una discrepancia grande de kilogramos es inadmisible. El sistema actual muestra alerta roja y pide confirmar un cambio; los errores hoy son poco frecuentes. | Simular rechazo de órdenes dudosas y un flujo visible de excepción. No presentar una simple confirmación por voz como autorización suficiente para una desviación real. |
| Accionamiento, 10:24–11:02 | Brazo y manguera se extienden/retraen hidráulicamente desde un botón de cabina. Hay controles administrativos de distancia, sensores de proximidad y cámaras 360°. | En el simulador, cada comando de movimiento depende del estado y de interbloqueos **ficticios y claramente rotulados**. No asumir acceso a los sensores reales. |
| Mandos, 25:40–26:12 y 28:25–29:05 | Voz y mando manual no deben operar simultáneamente; si la voz falla, el operador puede detenerse e inhabilitarla para volver al modo manual mientras se repara. | Modelar modos exclusivos y transferencia explícita. La prioridad eléctrica real de controles físicos y parada de emergencia queda pendiente de ingeniería de seguridad. |
| Emisor, 26:15–26:43 | El representante quiere órdenes solo del operador responsable de esa unidad. | Mostrar sesión de operador autenticado en la demo. La identificación fiable de una persona por voz necesita requisitos y validación aparte; el ASR por sí solo no autentica. |
| Respuesta al operador, 26:43–27:40 | Desea confirmaciones breves de ejecución: si avanzó o no, si retrajo la manguera, si terminó el carguío. | Respuestas cortas, inequívocas y ligadas al estado confirmado por el simulador; no decir “hecho” al mero reconocimiento de la frase. |
| Entorno acústico, 07:05–07:55 y 29:40–30:08 | La operación se hace en cabina cerrada. Se usa radio tipo handy cuando hace falta; el representante comparó el ruido con el de un vehículo común. No dio medición exacta utilizable para diseñar. | Probar primero micrófono de cabina/auricular con ruido representativo. Casco con micrófono de garganta y LoRa no resultaron requisitos del briefing. |
| Comunicaciones, 04:40–05:30 y 17:05–17:45 | La congestión del handy involucra a muchos equipos de la mina, pero no afecta directamente el comando local de carguío. Para datos, ORICA mencionó celular o Starlink y restricciones para usar la red de la mina. | Mantener el reconocimiento y las reglas locales; no basar la orden de movimiento en radio de largo alcance ni en nube. La integración de datos queda por definir. |
| Interfaz del equipo, 11:10–11:43 y 15:51–17:00 | No conocía en ese momento marca/protocolo de la pantalla o PLC, ni confirmó un puerto utilizable. Pidió enviar la pregunta al comité. En la conversación se mencionaron LOADPlus y equipos Tread/ProBlast como referencias. | Adaptador de equipo **simulado** hasta que ORICA entregue datos técnicos y acceso autorizado. No afirmar compatibilidad con LOADPlus o ProBlast. |
| Material de observación, 19:15–20:49 | Dijo que podrían coordinar una vista de la operación mediante reunión, gestionada por organizadores. | Solicitarla por el comité para observar pantallas, secuencia y vocabulario reales; no asumir disponibilidad de archivos de audio. |
| Canal de información, 20:22–20:49 | El representante enviará información al comité organizador, que la compartirá con los equipos. | Centralizar preguntas técnicas y seguimiento por el comité. |

## 3. Definición propuesta de la versión 1

**Faro v1:** copiloto de comandos de voz local para el operador de una MMU, demostrado sobre una **unidad y malla simuladas**. El sistema escucha durante una sesión activada, reconoce frases de vocabulario cerrado, interpreta el taladro y la acción, verifica el estado simulado, solicita confirmación cuando corresponde, muestra el resultado y guarda un registro. La voz no escribe directamente al PLC ni ejecuta acciones físicas.

### Flujo demostrable

1. El operador abre sesión, elige modo voz y ve el taladro ficticio actual, cantidad y mezcla del plan.
2. Dice «consultar taladro 123». Faro lee y muestra el plan; si el ID no coincide, pide aclaración.
3. Dice «preparar carguío» o una acción de brazo/manguera definida para ese modo. El motor comprueba estado, taladro y señal ficticia de zona despejada.
4. La consola muestra **orden reconocida → validada → enviada al simulador → completada/rechazada**. La confirmación solo llega tras la respuesta del simulador.
5. Para cantidad/mezcla, Faro compara el dictado con el plan. Una discrepancia abre una excepción y no ejecuta un carguío simulado hasta resolverla según una regla explícita.
6. «Pausar» y «pasar al siguiente taladro» se prueban con las condiciones correspondientes. Un fallo de voz permite desactivar el modo voz y pasar al modo manual simulado.

El vocabulario exacto, qué acción se confirma dos veces y qué cambios requieren supervisor **no quedaron suficientemente definidos** en el briefing. Deben acordarse antes de congelar el flujo. La primera versión puede mostrar estos estados como propuestas de diseño y no como políticas vigentes de ORICA.

### Arquitectura recomendada

`Micrófono/auricular → ASR local → gramática e intención cerrada → motor de estados y reglas → adaptador de MMU simulada → interfaz/bitácora`

La consola de escritorio PySide6 y el reconocimiento local ya construidos son reutilizables. Hay que reemplazar el dominio de “revisión auxiliar” por `malla → taladro → preparación → carga simulada → cierre → siguiente`. El motor debe diferenciar transcripción, aceptación, inicio y finalización de una orden. Para acciones que puedan mover equipo o cargar explosivos, un modelo generativo no debe decidir la autorización. La voz local es una elección de diseño para continuidad operativa, no un requisito expreso de “100 % sin Internet” confirmado por ORICA.

## 4. Lo que aún necesitamos de ORICA

Enviar estas preguntas **a través del comité organizador**, idealmente con respuesta escrita:

1. **Acción prioritaria:** ¿Para la versión inicial prefieren demostrar extensión/retracción de brazo, manguera, selección de taladro o ingreso/confirmación de cantidad y mezcla? ¿Cuál es el criterio de éxito observable?
2. **Secuencia operativa:** ¿Pueden compartir una grabación de pantalla o una sesión guiada de un carguío típico y una excepción, con datos no sensibles?
3. **Límites de seguridad:** ¿Qué órdenes por voz están expresamente fuera de alcance? ¿Qué interbloqueos y parada física tienen prioridad? ¿Qué confirmación o autorización exige cada clase de orden?
4. **Datos del sistema:** ¿Qué modelo concreto de MMU/control se tomaría como referencia y qué señales de solo lectura o interfaz documentada podrían usarse en un piloto futuro? ¿Hay entorno de pruebas?
5. **Operador e identidad:** ¿Qué método de identificación y habilitación de sesión aceptan? ¿Qué sucede si otra persona habla dentro o cerca de la cabina?
6. **Condiciones de voz:** ¿Podrían compartir un registro autorizado del ruido de cabina, tipo de auricular/EPP y frases naturales que emplean los operadores? ¿Qué tasa máxima de falsa aceptación consideran tolerable?
7. **Excepciones de diseño:** Si el taladro real difiere del plan, ¿quién puede cambiar kilos/mezcla y cómo se registra y confirma esa decisión?

## 5. Prioridad de trabajo del equipo

**Ahora:** modelar la malla y taladros ficticios, dibujar el flujo de estados, actualizar la consola y escribir escenarios de aceptación/rechazo. Después, integrar el ASR local existente con frases específicas y medir latencia, errores de reconocimiento y falsas aceptaciones con voces distintas. Luego, ensayar en una cabina simulada con ruido representativo. Una integración con hardware o PLC solo tendría sentido tras recibir especificaciones, autorización y revisión de seguridad de ORICA.

**Criterio de avance:** la demo debe mostrar un ciclo completo por taladro y al menos cuatro fallos controlados: ID incorrecto, kilos fuera del plan, persona próxima según sensor ficticio y pérdida/fallo de voz. Debe distinguir órdenes reconocidas de operaciones realmente terminadas en el simulador.

## 6. Referencias públicas de contexto

- [ORICA, Bulkmaster y MMU](https://www.orica.com/en/blasting-solutions/delivery-systems/surface-delivery-systems/bulkmaster): describe la unidad móvil y su relación con el carguío de taladros.
- [ORICA, LOADPlus](https://www.orica.com/ArticleDocuments/2705/Orica_LOADPlus%20Flyer_Final.pdf.aspx): muestra funciones de diseño por taladro, reglas de carguío y registro de datos; no documenta aquí una API pública para Faro.
- [ORICA, ficha de MMU para Latinoamérica](https://www.orica.com/ArticleDocuments/2605/200685_Flyer_MMU_LatAm_A4_WEB.pdf.aspx): lista Tread 4219 con ProBlast como referencia de producto. No confirma que sea la unidad concreta del reto.
