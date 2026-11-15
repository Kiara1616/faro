# Auditoría de estado GitHub F-01–F-20

Fecha de consulta: 2026-11-15  
Repositorio: `Kiara1616/faro`  
Fuente: consulta directa de GitHub (`fetch_issue`) para cada issue.

| Issue | Estado remoto | Comentarios | Lectura de cierre |
|---|---|---:|---|
| F-01 | Cerrada | 8 | Criterio documental y revisión cruzada registrados; preguntas ORICA siguen pendientes sin atribuir aprobación. |
| F-02 | Abierta | 6 | Código y pruebas aprobados; falta revisión manual conjunta voz/lógica/UI. |
| F-03 | Cerrada | 4 | Fixture, esquema, negativos y determinismo documentados. |
| F-04 | Cerrada | 3 | Motor de estados y transiciones prohibidas cubiertos por pruebas. |
| F-05 | Cerrada | 4 | Adaptador simulado y eventos correlacionados por `command_id`. |
| F-06 | Cerrada | 4 | Excepciones y recuperación ficticia cubiertas. |
| F-07 | Cerrada | 3 | Sesión y modos voz/manual excluyentes cubiertos. |
| F-08 | Cerrada | 4 | Auditoría SQLite y exportación redactada verificadas. |
| F-09 | Cerrada | 4 | Parser cerrado, positivos/negativos y números verificados. |
| F-10 | Abierta | 7 | Integración local aprobada; falta ensayo hablado con ruido/EPP y desconexión física. |
| F-11 | Abierta | 4 | Evaluador preparado; falta corpus humano consentido y p50/p95. |
| F-12 | Abierta | 7 | Contrato UI offscreen aprobado; falta recorrido/captura manual. |
| F-13 | Abierta | 7 | Estados y alertas cubiertos automáticamente; falta ensayo visual manual. |
| F-14 | Abierta | 4 | Mensajes y fallback implementados; faltan dos usuarios, ergonomía y decisión TTS. |
| F-15 | Abierta | 8 | Integración y escenarios automatizados; falta recorrido manual de dos taladros. |
| F-16 | Abierta | 9 | Diagnóstico, modelo y CI listos; falta copia limpia, red desconectada y reinicio. |
| F-17 | Abierta | 6 | Matriz actualizada; faltan métricas humanas y revisión cruzada final. |
| F-18 | Abierta | 5 | Protocolo preparado; faltan dos participantes no autores. |
| F-19 | Abierta | 4 | Guion y FAQ preparados; falta ensayo cronometrado con acta. |
| F-20 | Abierta | 20 | Manifiesto/CI listos; faltan gates finales y tag de entrega. |

## Verificación cruzada

- La tabla coincide con el estado remoto consultado el 2026-11-15.
- No se cerró ninguna issue con evidencia humana pendiente.
- Las issues abiertas conservan comentarios con commit, pruebas, revisión,
  límites y responsable de la siguiente evidencia.
- El estado `simulation_only=true` se mantiene; no hay conectores industriales.
