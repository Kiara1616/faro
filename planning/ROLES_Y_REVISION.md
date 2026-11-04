# Faro — responsabilidades y revisión de issues

**Fecha:** 3 de noviembre de 2026 · **Entrega objetivo:** 10 de noviembre de 2026.

Este reparto define funciones de trabajo, no identidades ni acreditaciones profesionales del equipo. Los subagentes aportan implementación y revisión de software. La operación y la seguridad industrial de una MMU real requieren especialistas y autorización de ORICA.

| Frente | Papel completo | Artefactos que lidera | Revisión que debe solicitar |
| --- | --- | --- | --- |
| Coordinación e integración | Ordena issues, mantiene contratos entre módulos, integra cambios, ejecuta CI y publica comentarios de avance con evidencia. | F-05, F-08, F-15, F-16, F-20 y documentación transversal. | QA y seguridad del simulador para cambios de estado; producto para afirmaciones del briefing. |
| Dominio y simulación | Modela estados, comandos, eventos y adaptador ficticio; conserva invariantes y rechazos sin mutación; escribe pruebas deterministas. | F-04 a F-06, F-21 a F-24. | Seguridad del simulador y QA, con casos de concurrencia, duplicados y fallo. |
| Producto y seguridad del simulador | Contrasta alcance y decisiones con el briefing; detecta supuestos, mensajes engañosos y reglas sin respaldo; revisa riesgos de control simulado. | F-01, F-02, F-17, F-19 y revisión de dominio. | Integración para viabilidad; ORICA para cualquier conclusión sobre operación real. |
| Voz, interfaz y QA | Revisa vocabulario, ASR local, falsas aceptaciones, claridad de estados, accesibilidad básica y ensayos adversos. Diseña matriz de pruebas y evidencia. | F-09 a F-14, F-18, F-25, F-28. | Dominio para interpretación y autorización; producto para lenguaje operacional. |

## Ciclo de cada issue

1. Leer objetivo, dependencias y criterios; identificar qué se puede comprobar con datos ficticios y qué requiere respuesta de ORICA.
2. Implementar en una superficie de archivos asignada y añadir pruebas que demuestren el comportamiento, especialmente rechazo y recuperación.
3. Ejecutar las pruebas relevantes; revisar código, documentación, mensajes y resultados contra el contrato del issue. Corregir cualquier incongruencia y repetir las pruebas afectadas.
4. Solicitar revisión cruzada a otro frente. Registrar observaciones y cambios; repetir la revisión hasta resolver las observaciones verificables.
5. Publicar comentario en el issue con commit/PR, archivos, pruebas, resultado, límites y pendientes. Leer de nuevo el comentario y el estado del issue. Cerrar solo si la evidencia cubre todos los criterios y la revisión requerida terminó.

Los subagentes no son sustitutos de un operador o ingeniero de seguridad de ORICA. Si falta esa validación, el issue puede quedar listo para revisión interna pero no se declara validado para uso industrial.
