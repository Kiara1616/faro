# Protocolo de comprensión de la consola Faro

Propósito: descubrir confusiones de interfaz antes del pitch. Esto evalúa la
claridad de la demo con miembros del equipo; no valida la operación minera ni
la seguridad de un equipo real.

## Preparación

- Participantes: mínimo dos personas que no hayan implementado `faro/ui.py`.
- Entorno: copia fijada del repositorio, malla ficticia y comandos escritos o
  micrófono autorizado. No recopilar nombres completos, audio ni datos de salud.
- Observador: una persona toma tiempos y no da pistas salvo para recuperar la
  aplicación si se bloquea.
- Estado inicial: sesión manual, sin taladro seleccionado, historial vacío.

## Guion sin pistas

Leer únicamente cada tarea y pedir que la persona explique en voz alta qué ve:

1. Selecciona el taladro 101 y consulta su estado.
2. Prepara la carga y declara producto alfa, 100 kg.
3. Intenta extender el brazo sin confirmar que la zona está libre.
4. Explica la diferencia entre «reconocido», «aceptado», «en ejecución» y
   «completado».
5. Ejecuta el mismo movimiento con la señal ficticia de zona libre y espera el
   estado completado.
6. Intenta iniciar carga con producto beta y describe qué debe hacer ante el
   rechazo.

Registrar para cada tarea: inicio, fin, segundos, primer intento correcto,
errores, ayuda recibida, frase que la persona cree que ocurrió y estado real.

## Hoja de resultados anonimizada

| Participante | Tarea | Tiempo (s) | Error / confusión | Estado que creyó | Estado real | Cambio propuesto |
|---|---|---:|---|---|---|---|
| P-01 | 1–6 | — | Pendiente de ejecución | — | — | — |
| P-02 | 1–6 | — | Pendiente de ejecución | — | — | — |

## Puerta de decisión

- Si alguien confunde «aceptado» con «completado», cambiar el texto visible y
  repetir las tareas 3–5 hasta que lo explique correctamente.
- Si alguien cree que un rechazo ejecutó la orden, hacer más prominente el
  estado `rechazado`, el motivo y que no se envió al simulador.
- Si el tiempo o el error se debe a una instrucción ambigua, corregir la UI o
  el guion; no entrenar al participante con explicaciones adicionales.
- Adjuntar capturas antes/después y fecha de repetición, sin datos personales.

## Registro de revisión

| Versión | Cambio | Motivo | Repetición | Resultado |
|---|---|---|---|---|
| 8dc8bfc | Protocolo inicial | F-18 | Pendiente | Pendiente |

