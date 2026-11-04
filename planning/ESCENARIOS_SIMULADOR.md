# Escenarios reproducibles del simulador

Los escenarios de [`fixtures/escenarios_demo.json`](../fixtures/escenarios_demo.json)
son ficticios y no representan señales de una MMU real. Se cargan con
`faro.scenarios.load_scenarios()` y producen siempre los mismos parámetros.

| Nombre | Propósito | Parámetros |
|---|---|---|
| `normal` | Caso base | demora 1 tick, sin fallos |
| `zona_ocupada` | Verificar fail-closed | la coordinación no pasa `zone_clear` |
| `fallo_brazo` | Fallo inyectado | `extender_brazo` termina en `failed` |
| `demora_timeout` | Respuesta no confiable | demora 10, timeout 2; termina en `unknown` |
| `adaptador_lento` | Demora tolerable | demora 3, sin timeout |

Cada ensayo debe crear un simulador nuevo, ejecutar el caso dos veces, comparar
estado/eventos y después crear otro con `normal`. No se reutilizan objetos entre
escenarios: así se evita contaminación de fallos anteriores. Los nombres deben
permanecer visibles como **SIMULACIÓN** en cualquier selector de UI futuro.

Verificación automatizada: `tests/test_scenarios.py`; suite actual: 150 pruebas.

