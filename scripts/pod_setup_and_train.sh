#!/bin/bash
# Full quality training - fixed arguments + dataset sync
set -e

echo "=== GenAudius FULL QUALITY Training - RTX 4090 ==="
WORK=/workspace/GenAudius_V1
cd $WORK

echo "[1/7] System deps (skip if done)..."
apt-get install -y -qq pkg-config libavcodec-dev libavformat-dev libavutil-dev \
    libswscale-dev libavdevice-dev libavfilter-dev libswresample-dev 2>/dev/null || true

echo "[2/7] PyTorch 2.1.0 (AudioCraft compatible)..."
pip install -q --root-user-action=ignore \
    torch==2.1.0 torchaudio==2.1.0 torchvision==0.16.0 \
    --index-url https://download.pytorch.org/whl/cu121

echo "[3/7] AudioCraft core deps..."
pip install -q --root-user-action=ignore \
    "numpy<2.0.0" av==11.0.0 protobuf "spacy==3.7.6" \
    pesq pystoi torchdiffeq torchmetrics "torchtext==0.16.0" || true

echo "[4/7] AudioCraft (no-deps)..."
pip install -q --no-deps --root-user-action=ignore \
    git+https://github.com/facebookresearch/audiocraft.git
pip install -q --root-user-action=ignore \
    flashy hydra-core hydra-colorlog julius num2words \
    scipy sentencepiece transformers tqdm demucs librosa encodec

echo "[5/7] GenAudius runtime..."
pip install -q --root-user-action=ignore \
    runpod "pydantic<2.0.0" python-dotenv soundfile \
    pyloudnorm basic-pitch pedalboard mido spotipy pylast \
    "fastapi==0.99.1" uvicorn

echo "[6/7] Syncing dataset from GitHub (manifests + audio)..."
# Fetch stems from git (they're in the repo since we pushed them)
cd $WORK
git pull origin main 2>&1 | tail -3

# Rebuild manifests now that audio is in place
python3 musicgau/train/build_manifests.py

# Verify we have data
ENTRIES=$(python3 -c "import gzip,json; f=gzip.open('datasets/bachata_stems_v1/manifests/train.jsonl.gz','rt'); lines=f.readlines(); print(len(lines))")
echo "Dataset entries: $ENTRIES"

echo "[7/7] Launching FULL QUALITY training (NO dry-run)..."
export GAU_API_KEY="gau_master_secure_2026"
export PYTHONPATH="/workspace/GenAudius_V1:$PYTHONPATH"
export USER="root"

mkdir -p /workspace/checkpoints/bachata_v1_full

# Correct CLI: subcommand 'train' + --no-dry-run + all options
nohup python3 musicgau/train/run_audiocraft.py train \
    --dataset-root datasets/bachata_stems_v1 \
    --out-dir /workspace/checkpoints/bachata_v1_full \
    --max-steps 50000 \
    --batch-size 8 \
    --lr 0.0001 \
    --no-dry-run \
    --device cuda \
    > /workspace/training.log 2>&1 &

TRAIN_PID=$!
echo $TRAIN_PID > /workspace/train.pid

sleep 5
echo ""
echo "=============================================="
echo "FULL QUALITY TRAINING STARTED!"
echo "PID: $TRAIN_PID | Steps: 50k | Batch: 8"
echo "=============================================="
echo "--- First log lines ---"
head -20 /workspace/training.log 2>/dev/null || echo "(log empty - loading model...)"
echo ""
echo "GPU utilization:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader
