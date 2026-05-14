#!/bin/bash
pkill -9 -f "python3 musicgau" 2>/dev/null || true
sleep 2
cd /workspace/GenAudius_V1
nohup python3 musicgau/train/direct_train.py > /workspace/direct_training.log 2>&1 &
echo $! > /workspace/train.pid
echo "PID: $(cat /workspace/train.pid)"
sleep 20
echo "=== LOG ==="
tail -25 /workspace/direct_training.log
echo "=== GPU ==="
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
