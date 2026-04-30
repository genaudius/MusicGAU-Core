# MusicGAU: RunPod Serverless Training

Esta guía explica cómo configurar el entrenamiento de MusicGAU como un Endpoint de **RunPod Serverless**.

## 1. Preparación de la Imagen

La imagen ya está preparada para soportar tanto el modo interactivo (Pod) como el modo Serverless.

### Build local:
```bash
docker build -t musicgau-train:serverless .
```

### Push al registro:
```bash
docker tag musicgau-train:serverless tu-usuario/musicgau-train:latest
docker push tu-usuario/musicgau-train:latest
```

## 2. Configuración en RunPod

### A. Network Volume
Es **CRÍTICO** usar un Network Volume para que los datos y los checkpoints no se pierdan.
1. Crea un Network Volume en RunPod (ej: `musicgau-data`).
2. Sube tu dataset a este volumen (puedes usar un Pod temporal para esto).
3. Asegúrate de que la ruta sea consistente (ej: `/workspace/data`).

### B. Serverless Endpoint
1. Ve a **Serverless** -> **Endpoints**.
2. **Container Image**: `tu-usuario/musicgau-train:latest`.
3. **Container Disk**: 10GB-20GB.
4. **Environment Variables**:
   - `RUNPOD_SERVERLESS`: `true`
   - `PYTHONPATH`: `/workspace/GenAudius_V1`
5. **Volume Mount**:
   - Selecciona tu Network Volume.
   - Mount Path: `/workspace/data` (Ajusta `dataset_root` en tu petición para que apunte aquí).

## 3. Ejecución (API Request)

Para iniciar un entrenamiento, envía un POST al endpoint de RunPod:

```json
{
  "input": {
    "dataset_root": "/workspace/data/bachata_stems_v1",
    "out_dir": "/workspace/data/out/musicgau_bachata",
    "max_steps": 2000,
    "batch_size": 4,
    "lr": 0.0001
  }
}
```

### Notas Importantes:
- **Timeouts**: Los entrenamientos largos pueden exceder el tiempo de espera por defecto de los endpoints. RunPod Serverless Jobs pueden durar hasta 24h, pero asegúrate de monitorear los logs.
- **Dora/Hydra**: El sistema usa Dora para trackear experimentos. Los resultados se guardarán en `out_dir`.
- **Resume**: Si el job se interrumpe y lo relanzas con el mismo `out_dir`, AudioCraft intentará resumir el entrenamiento automáticamente.
