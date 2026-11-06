# Acta de revisión de invariantes F-21

Fecha: 2026-11-06  
Revisión: producto/seguridad + lógica  

Se revisó `planning/INVARIANTES.md`, `faro/domain.py`, `faro/simulator.py`,
`faro/controller.py` y sus pruebas. Las 11 invariantes están expresadas como
condiciones verificables y no se presentan como controles industriales.

| Aspecto | Resultado |
|---|---|
| Rechazo sin mutación | Verificado en pruebas de dominio |
| Una acción activa y correlación por ID | Verificado |
| Zona fail-closed y plan exacto | Verificado |
| Fallo, cancelación y timeout | Verificado |
| Diferencia entre pausa simulada y paro físico | Rotulada en documentación/UI |
| Mensajes de aceptación/ejecución/finalización | Catálogo probado; revisión visual manual pendiente |

Conclusión: aprobado para el alcance del simulador. Cualquier control físico,
interlock o paro de emergencia requiere requisitos y validación de ORICA.

