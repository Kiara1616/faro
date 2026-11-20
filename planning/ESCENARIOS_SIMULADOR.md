# Escenarios reproducibles del simulador

Los escenarios de [`fixtures/escenarios_demo.json`](../fixtures/escenarios_demo.json)
son ficticios y no representan señales de una MMU real. Se cargan con
`faro.scenarios.load_scenarios()` y producen siempre los mismos parámetros.

| Nombre | Propósito | Parámetros |
|---|---|---|
| `normal` | Caso base | demora 1 tick, sin fallos |
| `zona_ocupada` | Verificar rechazo por zona ficticia ocupada | el escenario fija `zone_clear_available=false`; el controlador rechaza el movimiento aunque se solicite `zone_clear=true` |
| `fallo_brazo` | Fallo inyectado | `extender_brazo` termina en `failed` |
| `demora_timeout` | Respuesta no confiable | demora 10, timeout 2; termina en `unknown` |
| `adaptador_lento` | Demora tolerable | demora 3, sin timeout |

Cada ensayo debe crear un simulador nuevo, ejecutar el caso dos veces, comparar
estado/eventos y después crear otro con `normal`. No se reutilizan objetos entre
escenarios: así se evita contaminación de fallos anteriores. Los nombres deben
permanecer visibles como **SIMULACIÓN** en cualquier selector de UI futuro.

La consola permite seleccionar el escenario ficticio mediante la variable local
`FARO_SCENARIO` antes de iniciar (`normal` por defecto). La tarjeta de operación
muestra el nombre del escenario junto al taladro y el registro incorpora el
escenario en el motivo del evento. Un nombre desconocido vuelve a `normal`; no
se acepta una configuración no validada.

Verificación automatizada: `tests/test_scenarios.py` y pruebas del controlador.
La suite de UI se ejecuta con `QT_QPA_PLATFORM=offscreen`.

