#!/usr/bin/env bash
# Run MusicGen training from repo root (GenAudius_V1). Intended for RunPod / Linux.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export USER="${USER:-root}"

exec python -m musicgau.train.run_audiocraft train \
  --dataset-root "${DATASET_ROOT:-datasets/bachata_stems_v1}" \
  --out-dir "${OUT_DIR:-checkpoints/musicgau_bachata}" \
  --no-dry-run \
  --max-steps "${MAX_STEPS:-5000}" \
  --batch-size "${BATCH_SIZE:-4}" \
  "$@"
