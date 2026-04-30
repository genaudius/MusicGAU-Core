# RunPod (Linux GPU) — entrenamiento MusicGAU

## 1. Datos en un volumen

En el pod, coloca el dataset bajo el mismo layout que en local, por ejemplo:

`/workspace/data/bachata_stems_v1/manifests/...` y clips referenciados en los manifests.

## 2. Build de la imagen

Desde la raíz de `GenAudius_V1` (donde está el `Dockerfile`):

```bash
docker build -t musicgau-train:latest .
```

Opcional: fijar rama de AudioCraft si `main` falla:

```bash
docker build --build-arg AUDIOCRAFT_REF=v1.3.0 -t musicgau-train:latest .
```

## 3. RunPod

- **Container disk**: monta un **Network Volume** (o disco persistente) con tu `datasets/`.
- **Start command** (ejemplo): entra al cwd del repo y apunta `DATASET_ROOT` al volumen.

Si clonas el repo en el pod y el dataset está en `/workspace/data`:

```bash
export USER=root
export DATASET_ROOT=/workspace/data/bachata_stems_v1
export OUT_DIR=/workspace/data/out/musicgau_bachata
cd /workspace/GenAudius_V1   # o la ruta donde esté el repo
./scripts/runpod_train.sh
```

O con Docker local equivalente:

```bash
docker run --gpus all -it --rm \
  -v /ruta/local/bachata_stems_v1:/workspace/data/bachata_stems_v1:ro \
  -v /ruta/local/out:/workspace/out \
  -e DATASET_ROOT=/workspace/data/bachata_stems_v1 \
  -e OUT_DIR=/workspace/out/musicgau_bachata \
  -e USER=root \
  musicgau-train:latest
```

## 4. Hugging Face

EnCodec / pesos se descargan desde Hugging Face. Si hace falta token:

```bash
huggingface-cli login
```

## 5. Presets Hydra

Los YAML `musicgau_bachata_32khz` y `musicgau_bachata_mono_32khz` se copian al build en `audiocraft/config/dset/audio/`. Las rutas dentro del YAML son relativas al **cwd** al entrenar (`datasets/...`); por eso `DATASET_ROOT` debe coincidir con `datasets/bachata_stems_v1` bajo ese cwd, o usa un symlink:

```bash
ln -sfn "$DATASET_ROOT" datasets/bachata_stems_v1
./scripts/runpod_train.sh --dataset-root datasets/bachata_stems_v1
```
