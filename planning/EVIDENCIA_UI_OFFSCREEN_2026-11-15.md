# Evidencia de smoke UI offscreen

Fecha: 2026-11-15  
Commit de referencia: `ad53c94`  
Entorno: Windows 11 · Python 3.12.10 · `QT_QPA_PLATFORM=offscreen`

## Comando ejecutado

Se creó `QApplication`, se instanció `FaroWindow`, se renderizó una instantánea
del escenario normal con taladro 101 y se cerró el event loop mediante un
`QTimer`. Se verificó programáticamente que la insignia visible fuera:

```text
SIMULACIÓN - SIN CONEXIÓN A EQUIPO
```

Salida observada:

```text
Qt smoke UI OK
```

## Alcance

Esta evidencia confirma que la UI puede inicializarse y renderizar una vista
ficticia en modo headless. No demuestra legibilidad a distancia, contraste con
usuarios, comprensión, comportamiento con auricular ni una sesión de voz real;
esas pruebas siguen en `planning/PLAN_VALIDACION_MANUAL.md`.
