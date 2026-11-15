# F-25 — Fallos de audio y estado real de escucha

## Implementado

- `VoiceRecognizer.capture_state` expone `stopped`, `starting`, `listening` o
  `error` según el trabajador real.
- `last_error` conserva el motivo técnico sin guardar audio.
- Cada transcripción final puede transportar la generación de la captura que
  la produjo; una respuesta encolada no adopta la generación de una escucha
  posterior.
- Modelo ausente, dependencia faltante, dispositivo inválido o excepción de
  captura emiten `error` y después cierran el recurso con `stopped`.
- `start()` no crea un segundo hilo mientras el anterior sigue vivo; después
  de un fallo terminado permite un reintento explícito.
- Un watchdog configurable detecta que el stream dejó de entregar fragmentos;
  el error detiene el consumo y cierra el recurso.
- La apertura del dispositivo se serializa con la solicitud de parada: si la
  parada llega durante el constructor del stream, este se cierra sin emitir
  `listening`.
- Los callbacks de estado también llevan la generación y la UI descarta
  estados tardíos de una captura anterior.
- `app.py` conserva el mensaje de error tras el callback final `stopped`, para
  no mostrar una escucha aparentemente activa o un cierre ambiguo.

## Pruebas automatizadas

- Modelo ausente: error útil, estado final `stopped`, `last_error` conservado.
- Reintento tras fallo: dos ciclos `starting → error → stopped`, sin hilo
  duplicado.
- Stream silencioso simulado: watchdog produce error y termina el trabajador.
- Callback de resultado fallido: activa parada fail-closed.
- Configuración de audio inválida: rechazo antes de iniciar.
- CI Windows: la suite y la importación Qt se ejecutan en el workflow.

## Límite de evidencia

La desconexión física, permisos del dispositivo y una frase hablada deben
ensayarse en la laptop de demostración. No se inventa una transcripción ni se
afirma exactitud de voz. Mientras la captura falla, la entrada escrita sigue
disponible y el operador debe reintentar explícitamente.
