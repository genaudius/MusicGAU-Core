#!/bin/bash
set -e
cd /workspace/GenAudius_V1

echo "=== Rebuilding manifests ==="
python3 musicgau/train/build_manifests.py

echo ""
echo "=== Verifying dataset ==="
python3 - <<'PYEOF'
import gzip
with gzip.open("datasets/bachata_stems_v1/manifests/train.jsonl.gz", "rt") as f:
    lines = f.readlines()
print(f"Train entries: {len(lines)}")
PYEOF

echo ""
echo "=== Launching FULL QUALITY training ==="
export GAU_API_KEY="gau_master_secure_2026"
export PYTHONPATH="/workspace/GenAudius_V1:$PYTHONPATH"
export USER="root"

mkdir -p /workspace/checkpoints/bachata_v1_full

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
echo ""
echo "Training PID: $TRAIN_PID"
sleep 8
echo "--- First training log lines ---"
head -30 /workspace/training.log
echo ""
echo "GPU:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader
