#!/bin/bash
cd /workspace/audiocraft_repo
export PYTHONPATH=$PYTHONPATH:.
# Kill any previous training
pkill -9 -f "audiocraft.train" || true
# Launch official training
nohup python3 -m audiocraft.train \
    solver=musicgen/musicgen_base_32khz \
    dset=audio/bachata_v1 \
    ++dataset.batch_size=4 \
    ++dataset.num_workers=0 \
    ++schedule.total_updates=50000 \
    ++optim.lr=0.0001 \
    > /workspace/training_official.log 2>&1 &
echo $! > /workspace/train_official.pid
echo "Entrenamiento lanzado con PID: $(cat /workspace/train_official.pid)"
