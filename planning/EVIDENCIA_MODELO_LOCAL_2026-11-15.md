# Inventario del modelo Vosk local

Fecha: 2026-11-15  
Ruta: `models/vosk-model-small-es-0.42`  
Alcance: artefacto preparado en la laptop; no es un hash oficial publicado por
Vosk ni prueba de que el modelo esté en GitHub.

## Conteo observado

- Archivos: `14`
- Tamaño total: `60,286,598` bytes
- `scripts/setup_voice_model.py --check`: `Modelo instalado`

## Hashes de archivos esenciales

| Archivo relativo | SHA-256 |
|---|---|
| `am/final.mdl` | `FF9508E4DB01D2E2375DA3887973F94EF8057EE85411F4CB10A5C174CE7A4425` |
| `conf/model.conf` | `330C1B50575D0C1C0402276C9CDC7A589EBD04DE5D3DE17695DD7E6DB701DA54` |
| `graph/HCLr.fst` | `CE42FBA42B99076F16BFE2892C3CAB0936FB7409EDBA95C545BE81C74F2F59E5` |
| `graph/Gr.fst` | `0DDC8AACBC80B2E8D470060A429EB26706B2AE1D32615A499BEFD60CC86A0304` |

El segundo revisor debe recalcular estos hashes en la carpeta que se entregue.
Si difieren, el paquete no se considera congelado. No se debe confundir este
inventario local con una medición de reconocimiento de voz ni con aprobación
industrial.
