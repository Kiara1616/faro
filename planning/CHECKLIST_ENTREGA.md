# Checklist de congelamiento de entrega Faro

Este documento se ejecuta antes de crear el tag final. No reemplaza el ensayo
manual ni autoriza una conexión a maquinaria real.

El procedimiento paso a paso y las hojas de registro están en
`planning/PLAN_VALIDACION_MANUAL.md`.

## 1. Identidad de la versión

- [ ] Registrar commit exacto y tag (`faro-demo-YYYYMMDD`).
- [ ] Guardar `git status --short` vacío.
- [ ] Registrar URL del CI Windows exitoso asociado al commit.
- [ ] Guardar `python --version`, versión de Windows y fecha/hora de ensayo.

## 2. Contenido que debe acompañar la copia

- [ ] Código `faro/`, `app.py`, `fixtures/malla_demo.json`.
- [ ] `models/vosk-model-small-es-0.42` completo o instrucciones de instalación
  verificadas previamente.
- [ ] `requirements.txt`, `requirements-voice.txt`, `requirements-dev.txt`.
- [ ] `README.md`, arquitectura, contrato, resultados y guion de pitch.
- [ ] `data/` limpia o una copia explícitamente marcada como evidencia; nunca
  incluir audio ni datos personales.

## 3. Verificación reproducible

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\diagnose_offline.py --json > work\diagnostico-offline.json
.\.venv\Scripts\python.exe app.py
```

Con la red desactivada: completar un caso normal, ejecutar un rechazo por
producto/kg, reiniciar y repetir. Si falla micrófono, usar el recorrido por
teclado y registrar el diagnóstico; no inventar una transcripción.

## 4. Manifiesto y hash

Desde la raíz del repositorio, guardar un listado de archivos y SHA-256 de la
copia entregada. Excluir `.git`, `.venv`, cachés, SQLite temporal y archivos de
audio. El hash se coteja contra la copia que revisa el segundo integrante.

```powershell
Get-ChildItem -Recurse -File faro,fixtures,planning,scripts,models |
  Get-FileHash -Algorithm SHA256 |
  Export-Csv work\manifest-sha256.csv -NoTypeInformation
```

## 5. Responsables y defectos conocidos

| Área | Responsable | Evidencia | Estado |
|---|---|---|---|
| Reglas y simulador | Integración/dominio | 190 pruebas locales; escenarios V-12/V-13; CI run 43766090956 | Confirmar en ensayo |
| Voz local | Voz/QA | diagnóstico + corpus autorizado | Micrófono real pendiente |
| UI y fallback | Producto/interfaz | pitch + prueba de comprensión | Participantes pendientes |
| Seguridad y límites | Producto/seguridad | contrato + matriz | Revisión cruzada pendiente |

Defectos conocidos: no hay autenticación biométrica, no existe conector
industrial, no se han medido ruido minero/EPP y el modelo Vosk debe estar
instalado antes del ensayo offline.

## 6. Aprobación cruzada

| Revisor | Fecha | Cotejó commit/manifiesto | Ejecutó caso normal | Ejecutó rechazo | Firma |
|---|---|---|---|---|---|
| Pendiente | — | — | — | — | — |

