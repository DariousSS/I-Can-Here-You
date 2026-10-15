#!/usr/bin/env bash
# Overnight pretraining run (RTX 3060). Launch detached:
#   nohup bash run.sh > train.log 2>&1 &
# or inside tmux:  tmux new -s train 'bash run.sh'
set -euo pipefail
cd "$(dirname "$0")"
export HF_HOME=/media/joseph/Media/.hf-cache
export TOKENIZERS_PARALLELISM=false

exec ./.venv/bin/python -u train.py \
  --dataset_name tglcourse/CelebA-faces-cropped-128 \
  --resolution 128 \
  --train_batch_size 16 \
  --max_train_steps 60000 \
  --max_hours 13.5 \
  --output_dir /media/joseph/Media/diffusion128/runs/celeba128
