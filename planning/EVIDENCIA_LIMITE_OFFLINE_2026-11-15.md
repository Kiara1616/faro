# Verificación del límite offline del runtime

Comando:

```powershell
.\.venv\Scripts\python.exe scripts\check_offline_boundary.py --json
```

Resultado observado:

```json
{
  "simulation_only": true,
  "runtime_network_violations": [],
  "allowed_installer": "scripts/setup_voice_model.py"
}
```

La comprobación escanea `app.py`, `faro/` y `scripts/`, y permite únicamente
el instalador previo del modelo. Esto demuestra que el runtime del simulador no
contiene clientes de red conocidos; no demuestra que la red física de Windows
esté desconectada ni autoriza una integración industrial.
