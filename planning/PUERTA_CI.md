# Puerta de calidad CI

El workflow `.github/workflows/ci.yml` ejecuta en Windows/Python 3.12:

1. instalación de `requirements-dev.txt`;
2. suite completa `python -m pytest -q`;
3. importación de PySide6 con `QT_QPA_PLATFORM=offscreen`.

Además de `push` y `pull_request`, el workflow admite `workflow_dispatch` para
relanzar la misma verificación Windows sobre el commit final desde GitHub
Actions.

La suite cubre dos taladros, discrepancias, zona fail-closed, eventos tardíos,
timeout, reinicio, escenarios aislados, auditoría, controles de modo y estados
de UI. Los tests de audio real siguen siendo manuales y no se presentan como
resultado de CI.

## Criterio de bloqueo

Un push no se considera candidato si pytest falla, si la UI no importa en modo
offscreen o si una transición prohibida permite completar una acción. El enlace
al run exitoso y el hash del commit deben anotarse en el issue de integración.

