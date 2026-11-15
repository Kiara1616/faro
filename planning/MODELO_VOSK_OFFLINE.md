# Modelo Vosk local para la demo

Faro usa `vosk-model-small-es-0.42` para reconocimiento local en español. El
modelo no se descarga al arrancar y no se envía audio a Internet.

## Preparación antes de desconectar la red

Desde la raíz del repositorio, con Internet disponible únicamente durante la
preparación del entorno:

```powershell
.\.venv\Scripts\python.exe scripts\setup_voice_model.py
.\.venv\Scripts\python.exe scripts\setup_voice_model.py --check
```

El segundo comando debe imprimir `Modelo instalado` y terminar con código 0.
Si se proporciona un SHA-256 obtenido de una fuente confiable, se puede
verificar el ZIP durante la instalación:

```powershell
.\.venv\Scripts\python.exe scripts\setup_voice_model.py --sha256 <SHA256_OFICIAL>
```

El modelo preparado se copia junto con la entrega offline en
`models/vosk-model-small-es-0.42`. La carpeta `models/` se mantiene fuera de
Git por su tamaño; el `package_manifest.py` de la copia preparada incluye sus
archivos y detecta cualquier cambio. La entrega debe conservar el modelo ya
preparado o un artefacto ZIP obtenido y verificado antes de desconectar la red.

## Evidencia mínima

Registrar en el acta:

- salida de `--check`;
- versión de Windows/Python;
- SHA-256 del ZIP o del artefacto conservado;
- resultado del manifiesto de la copia preparada;
- confirmación de que la aplicación inicia sin red.

El inventario actual de esta laptop está en
`planning/EVIDENCIA_MODELO_LOCAL_2026-11-15.md`.

No se debe afirmar que el modelo está incluido en GitHub: la evidencia válida
es la copia offline preparada y su hash cotejado por una segunda persona.
