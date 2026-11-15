# Privacidad y exportación de evidencia

- Faro no guarda audio crudo; la bitácora SQLite contiene transcripción,
  decisión, estado y evento del simulador.
- Para presentar resultados se usa `scripts/export_audit.py`, que genera JSON
  con `simulation_only=true` y `audio_included=false`.
- Las voces humanas del corpus deben contar con consentimiento; los WAV no se
  suben al repositorio ni a la carpeta de entrega.
- SQLite de ensayo, WAV, logs y datos personales están excluidos por `.gitignore`.
- La limpieza de un ensayo consiste en retirar recursivamente su SQLite, WAV y
  logs fuera del repositorio; el comando rechaza la raíz de un repositorio y no
  sigue symlinks. El reporte exportado se conserva solo si está anonimizado,
  incluyendo operador, sesión y transcripción.

Para generar una copia anonimizada y limpiar artefactos de ensayo:

```powershell
python scripts/export_audit.py data/faro-audit.sqlite3 work/auditoria-ficticia.json
python scripts/clean_evidence.py work/evidencia
```

La redacción es predeterminada. `--unredacted` queda reservado para revisión
local y no debe usarse en una carpeta entregable.

## Conservación y acceso propuestos para el prototipo

Estas son reglas internas del equipo, no una política aprobada por ORICA:

- La SQLite de desarrollo se conserva solo durante la depuración y el ensayo;
  después se exporta una copia redactada y se limpia el artefacto local.
- El reporte redactado se mantiene hasta terminar la revisión del pitch y el
  traspaso; después se conserva únicamente si el equipo acuerda una finalidad
  documentada.
- El acceso queda limitado a integrantes del equipo de desarrollo/QA que
  necesitan revisar el simulador; no se comparte audio humano ni datos
  identificables.
- Cualquier corpus humano requiere consentimiento separado, etiqueta anónima y
  eliminación a solicitud del participante.

El archivo de briefing se conserva solo para trabajo interno y no forma parte
del paquete presentable; la carpeta de entrega se verifica mediante el
manifiesto y no debe incluirlo, WAV, SQLite, logs ni secretos.

