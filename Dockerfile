# MusicGAU / AudioCraft training image for RunPod (or any Linux + NVIDIA).
# Build from GenAudius_V1 repo root. Mount your dataset at runtime (see deploy/RUNPOD.md).

ARG PYTORCH_IMAGE=pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime
FROM ${PYTORCH_IMAGE}

# Pin with: docker build --build-arg AUDIOCRAFT_REF=v1.3.0 ...
ARG AUDIOCRAFT_REF=main

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git libsndfile1 pkg-config build-essential ffmpeg \
    libavcodec-dev libavformat-dev libavutil-dev libswscale-dev \
    libavdevice-dev libavfilter-dev libswresample-dev \
    && rm -rf /var/lib/apt/lists/*

# Install AV via conda (stable binary)
RUN conda install -y -c conda-forge ffmpeg av

# Clone AudioCraft
RUN set -eux; \
    if [ "${AUDIOCRAFT_REF}" = "main" ]; then \
      git clone --depth 1 https://github.com/facebookresearch/audiocraft.git /opt/audiocraft; \
    else \
      git clone --depth 1 --branch "${AUDIOCRAFT_REF}" https://github.com/facebookresearch/audiocraft.git /opt/audiocraft \
      || git clone --depth 1 https://github.com/facebookresearch/audiocraft.git /opt/audiocraft; \
    fi

WORKDIR /opt/audiocraft

# INSTALL WITHOUT DEPS to avoid 'av' compilation
RUN pip install --no-deps -e .

# Install necessary dependencies manually (excluding 'av' which is already in conda)
RUN pip install flashy hydra-core hydra-colorlog julius num2words numpy scipy sentencepiece transformers tqdm demucs librosa encodec pesq spacy antlr4-python3-runtime docopt dora_search basic-pitch pedalboard mido spotipy pylast torchcodec

WORKDIR /workspace
COPY . /workspace/GenAudius_V1

WORKDIR /workspace/GenAudius_V1
RUN pip install -r requirements-runpod.txt \
    && chmod +x scripts/runpod_train.sh

ENV PYTHONPATH=/workspace/GenAudius_V1:${PYTHONPATH}

# Default to the training script. For RunPod Serverless, override the CMD to:
# python -u deploy/runpod_handler.py
ENV RUNPOD_SERVERLESS=false
CMD ["sh", "-c", "if [ \"$RUNPOD_SERVERLESS\" = \"true\" ]; then python -u deploy/runpod_handler.py; else ./scripts/runpod_train.sh; fi"]
