# Faro — prototipo del Reto 3 ORICA

Aplicación de escritorio para demostrar interacción por voz en una **consola ficticia de carguío por taladro**. El proyecto se presentó inicialmente como SafeFlow AI y ahora se llama **Faro** para facilitar la invocación oral. No se conecta a maquinaria, PLC, LOADPlus, sistemas de iniciación ni controles físicos. La malla, productos, kilos, brazo, manguera y estados son datos de demostración; no son parámetros operativos de ORICA.

El [plan de integración](planning/PLAN_FARO_ORICA.md), la [arquitectura](planning/ARQUITECTURA_FARO.md) y el [backlog de issues](planning/ISSUES_FARO_ORICA.md) organizan ese cambio hasta la entrega del proyecto el 10 de noviembre.

El trabajo del equipo se coordina en los [issues del repositorio privado](https://github.com/Kiara1616/faro/issues); la rama principal ejecuta pruebas automáticas en Windows.

## Qué demuestra

- Una interfaz local con malla ficticia, taladro activo, producto, kg, método,
  sesión, modo, estado de ejecución, alertas y bitácora.
- Comandos de voz en español reconocidos sin Internet mediante Vosk, activados explícitamente por el usuario.
- El mismo motor determinista para comandos hablados o escritos: lista cerrada, contexto de tarea, rechazo de órdenes ambiguas y bloqueo ante discrepancias.
- Bitácora local en SQLite (`data/faro-audit.sqlite3`), además de historial visible. No guarda audio crudo.

## Preparación en Windows

Se requiere Python 3.10 o superior, micrófono y conexión a Internet **solo durante la instalación**. Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\setup_voice_model.py
.\.venv\Scripts\python.exe app.py
```

Para contribuir al código, instalar `requirements-dev.txt` en lugar de `requirements.txt` y ejecutar `python -m pytest -q`. El repositorio incluye una acción de CI para Windows y un `Dockerfile` destinado solo a pruebas sin interfaz ni micrófono. Docker no forma parte de la ejecución de Faro en la laptop.

Si el entorno ya está preparado, basta el último comando. El modelo español queda en `models/vosk-model-small-es-0.42`; se puede verificar sin descargar con:

```powershell
.\.venv\Scripts\python.exe scripts\setup_voice_model.py --check
```

Para usar un modelo en otra carpeta, configure `FARO_VOSK_MODEL` con su ruta antes de abrir la aplicación. Si no hay micrófono o modelo, la entrada escrita sigue disponible para demostrar las reglas. El botón **Activar escucha** inicia el micrófono; **Detener escucha** lo apaga.

Antes de una demostración sin red, ejecute el diagnóstico local (no descarga ni contacta servicios externos):

```powershell
.\.venv\Scripts\python.exe scripts\diagnose_offline.py
.\.venv\Scripts\python.exe scripts\diagnose_offline.py --json  # evidencia para el acta
```

El diagnóstico identifica Python/Windows, malla, modelo, dependencias y micrófonos. La ausencia de modelo, Vosk o micrófono deja disponible la entrada escrita; para abrir la consola gráfica sí se requiere PySide6.

Para elegir un auricular o micrófono externo, liste los dispositivos y establezca el índice antes de iniciar la aplicación:

```powershell
.\.venv\Scripts\python.exe scripts\list_audio_devices.py
$env:FARO_AUDIO_DEVICE="5"  # sustituir por el índice correcto
.\.venv\Scripts\python.exe app.py
```

La tecla **F8** también activa o detiene la escucha. Es un control de prueba; no equivale a una activación por voz validada.

Con la escucha ya activa, Faro espera **«Oye Faro»** antes de aceptar una orden. Se puede decir en una frase (`Oye Faro, consultar estado`) o decir primero «Oye Faro» y dar la orden siguiente dentro de seis segundos. Mientras espera, Vosk sigue procesando el audio localmente para detectar la frase de activación; las transcripciones sin el prefijo se ignoran y no se agregan a la bitácora. La escucha se activa y desactiva manualmente con el botón o F8.

## Guion corto de demostración

1. Seleccionar el taladro `101` y consultar su plan ficticio.
2. Preparar la carga y validar producto `alfa` y `cien kilos` contra el plan.
3. Marcar **Simular zona despejada**, solicitar `extender brazo`, confirmar y observar `aceptada → en curso → completada`.
4. Solicitar `iniciar carga`, confirmar, retraer y cerrar el taladro.
5. Avanzar al taladro `102` y repetir con `beta` y `ciento veinte kilos`.
6. Repetir con `FARO_SCENARIO=fallo_brazo`: el movimiento termina en `fallo`, no se marca cargado y queda auditado.

Todos los datos son ficticios y no representan especificaciones industriales.

## Componentes y responsables

| Frente | Responsabilidad | Tecnología |
| --- | --- | --- |
| Interacción de voz | Captura, transcripción y errores de micrófono | `sounddevice`, Vosk español local |
| Consola | Pantallas, estados, entrada y bitácora visible | PySide6 Essentials |
| Motor contextual | Lista de comandos, secuencia, contraste y rechazos | Python, reglas explícitas |
| Integración | Eventos entre hilos, arranque, datos locales y pruebas | Señales Qt, SQLite, pytest |

La interfaz emite órdenes y muestra snapshots. `faro/controller.py` coordina el flujo; `faro/voice_pipeline.py` conecta el parser con `faro/domain.py`; el dominio valida estados y reglas; `faro/simulator.py` devuelve eventos; y `faro/audit.py` conserva decisiones y resultados en SQLite. `faro/presentation.py` prepara el estado visible sin depender de Qt. `faro/voice.py` captura audio en un hilo y `app.py` entrega sus callbacks a Qt mediante señales.

La primera máquina de estados de revisión auxiliar se conserva en `faro/legacy/indicator_review.py` con sus pruebas en `tests/legacy/`. No forma parte de la aplicación Faro actual.

## IA local y límites de seguridad

El reconocimiento de voz Vosk es el componente de IA local: transforma audio en texto sin enviar audio a un servicio externo. Un LLM conversacional no es necesario para aceptar comandos. La aceptación depende de reglas explícitas y de una lista cerrada de intenciones. Esto evita que una frase libre, una respuesta inventada o un comando fuera de contexto cambie el estado simulado.

La escucha se activa manualmente, la interfaz siempre muestra el resultado y la bitácora registra aceptaciones y rechazos. La demo no tiene conectores a equipos industriales. La bitácora contiene transcripciones, así que para pruebas públicas deben usarse voces y datos autorizados; no se guarda el archivo de audio. No se afirma cumplimiento de normas ni aprobación de ORICA: antes de cualquier integración real se necesitarían requisitos y validación proporcionados por la empresa.

Una respuesta hablada local podría añadirse para navegación y lectura de estados después de medir si aporta valor con el EPP previsto; la pantalla seguirá siendo la fuente visible de confirmación. Un LLM local solo tendría sentido para consultas explicativas sobre información autorizada y nunca debería emitir directamente acciones al simulador o a un equipo.

## Verificación y próximos pasos

```powershell
.\.venv\Scripts\python.exe -m pytest -q
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_offline_validation.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_clean_copy.ps1
```

El segundo comando repite los gates automatizables de diagnóstico, suite,
escenarios, límite offline, compilación y manifiesto. No reemplaza la prueba
con personas, la desconexión física de red ni una validación industrial.
El tercer comando reconstruye una copia temporal desde Git, incorpora el
modelo local y repite los gates antes de eliminarla.

Antes del pitch: probar el micrófono y EPP reales, con varias voces y ruido representativo; medir comandos correctos, rechazos y activaciones accidentales; ensayar sin Internet. El reconocimiento con audio de prueba **no demuestra rendimiento en una operación minera**.

El briefing de ORICA ubicó el caso de uso en el carguío por taladro desde una unidad móvil, y Faro v1 ya representa ese flujo en un simulador. Siguen pendientes la validación con operadores, las condiciones reales de voz y EPP, el modelo concreto del equipo, las órdenes autorizables, las reglas de excepción y cualquier interfaz técnica para un piloto futuro.

## Evaluación reproducible de la voz

`scripts/evaluate_voice.py` lee un CSV de casos etiquetados y archivos WAV PCM mono a 16 kHz/16 bits. Informa transcripción exacta, latencia de inferencia, aceptación según el parser y el dominio activos, y falsas aceptaciones por condición. No simula la confirmación del controlador ni el resultado de la MMU. Un CSV usa `wav,expected_text,expected_accept,setup_commands`; `setup_commands` separa órdenes de preparación con `|`, y `zone_clear` puede marcar una señal ficticia para evaluar un movimiento. Los archivos WAV se guardan junto al CSV o se indican mediante rutas relativas.

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_voice.py work\casos.csv --output work\resultado-voz.json
```

No se deben interpretar resultados de audio sintético como desempeño con ruido minero, EPP o voces de operadores. Una evaluación previa del prototipo transcribió «Oye Faro, mostrar estado» con dos voces sintéticas en audio limpio; esa medición no valida el flujo actual. Por ahora la escucha se activa explícitamente.
