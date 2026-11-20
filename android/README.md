# Faro para Android

Este módulo empaqueta el simulador y la interfaz web de Faro en la tablet. El
servidor escucha únicamente en `127.0.0.1`; no requiere laptop ni Wi-Fi al
ejecutarse. La compilación se hace en una laptop con Android SDK y Gradle.

Desde PowerShell, ejecutar `./build-debug.ps1`. El script copia las fuentes
actuales de `faro/`, `fixtures/` y `web/` al módulo Android y genera
`app/build/outputs/apk/debug/app-debug.apk`.

La versión para tablet usa los botones y comandos escritos. No incluye la
interfaz de escritorio PySide ni la entrada de voz Vosk.

En la tablet, la app mantiene el servidor mientras su proceso siga vivo. Aún
falta persistir y recuperar el estado del recorrido cuando Android cierre el
proceso; la bitácora SQLite sí se guarda en el directorio privado de la app.
