#!/usr/bin/env python3
"""
GenAudius Direct Training Script
Uses AudioCraft's Python API directly (no Hydra/Dora/CLI needed).
Full quality: fine-tunes MusicGen on bachata stems.
"""
import os
import sys
import json
import gzip
import time
import logging
import torch
import torchaudio
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/workspace/training.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("GenAudius-Train")

# ---- Config ----
DATASET_ROOT = Path("/workspace/GenAudius_V1/datasets/bachata_stems_v1")
MANIFEST_FILE = DATASET_ROOT / "manifests" / "train.jsonl.gz"
CHECKPOINT_DIR = Path("/workspace/checkpoints/bachata_v1_full")
MAX_STEPS = 50000
BATCH_SIZE = 8
LR = 1e-4
SAMPLE_RATE = 32000
SEGMENT_DURATION = 15.0  # seconds
SAVE_EVERY = 500

def load_manifest(manifest_path: Path):
    entries = []
    with gzip.open(manifest_path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

def load_audio_segment(audio_path: Path, sr: int, duration: float):
    """Load and resample a single audio segment."""
    waveform, orig_sr = torchaudio.load(audio_path)
    if orig_sr != sr:
        waveform = torchaudio.functional.resample(waveform, orig_sr, sr)
    # Take mono
    if waveform.shape[0] > 1:
        waveform = waveform.mean(0, keepdim=True)
    # Trim/pad to exact duration
    target_len = int(sr * duration)
    if waveform.shape[1] > target_len:
        waveform = waveform[:, :target_len]
    elif waveform.shape[1] < target_len:
        pad = target_len - waveform.shape[1]
        waveform = torch.nn.functional.pad(waveform, (0, pad))
    return waveform  # [1, T]

def main():
    log.info("=" * 60)
    log.info("GenAudius FULL QUALITY Training")
    log.info(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    log.info(f"Steps: {MAX_STEPS} | Batch: {BATCH_SIZE} | LR: {LR}")
    log.info("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    # Load dataset
    log.info(f"Loading manifest from {MANIFEST_FILE}")
    entries = load_manifest(MANIFEST_FILE)
    log.info(f"Found {len(entries)} audio segments")

    # Load AudioCraft MusicGen model
    log.info("Loading MusicGen base model for fine-tuning...")
    try:
        from audiocraft.models import MusicGen
        model = MusicGen.get_pretrained("facebook/musicgen-small", device=device)
    except Exception as e:
        log.error(f"Failed to load MusicGen: {e}")
        log.info("Trying alternative import...")
        from audiocraft.models.musicgen import MusicGen
        model = MusicGen.get_pretrained("facebook/musicgen-small", device=device)

    log.info(f"Model loaded on {device}")
    
    # Set model to training mode
    lm = model.lm
    lm.train()
    
    # Optimizer
    optimizer = torch.optim.AdamW(lm.parameters(), lr=LR, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=MAX_STEPS)

    log.info("Starting training loop...")
    step = 0
    best_loss = float("inf")
    
    while step < MAX_STEPS:
        # Shuffle and batch
        import random
        random.shuffle(entries)
        
        batch_entries = entries[:BATCH_SIZE]
        
        try:
            # Load audio batch
            audio_tensors = []
            for entry in batch_entries:
                audio_path = DATASET_ROOT / entry["path"]
                if audio_path.exists():
                    wav = load_audio_segment(audio_path, SAMPLE_RATE, SEGMENT_DURATION)
                    audio_tensors.append(wav)
            
            if not audio_tensors:
                log.warning("No audio loaded for batch, skipping...")
                continue
                
            # Stack into batch [B, 1, T]
            audio_batch = torch.stack(audio_tensors, dim=0).to(device)
            
            # Encode audio with EnCodec
            with torch.no_grad():
                encoded, scales = model.compression_model.encode(audio_batch)
            
            # Prepare conditioning (text descriptions)
            descriptions = [e.get("description", "bachata") for e in batch_entries[:len(audio_tensors)]]
            
            # Forward pass through LM
            optimizer.zero_grad()
            
            # Encode the conditioning text via T5
            with torch.no_grad():
                attributes, _ = model._prepare_tokens_and_attributes(descriptions, None)
            
            with torch.autocast(device_type=device.split(":")[0], dtype=torch.float16):
                # Tokenize attributes for the LM
                tokenized = model.lm.condition_provider.tokenize(attributes)
                cfg_conditions = model.lm.condition_provider(tokenized)
                
                # LMOutput has (logits=[B, K, T, card], mask=[B, K, T])
                lm_output = model.lm.compute_predictions(
                    encoded,
                    conditions=[],
                    condition_tensors=cfg_conditions,
                )
                logits = lm_output.logits  # [B, K, T, card]
                mask = lm_output.mask      # [B, K, T] bool
                
                # Shift targets: predict next token
                # encoded: [B, K, T] -> targets
                B, K, T = encoded.shape
                card = logits.shape[-1]
                
                # Flatten for cross entropy: [B*K*T, card] vs [B*K*T]
                logits_flat = logits.reshape(-1, card).float()
                targets_flat = encoded.reshape(-1).long()
                mask_flat = mask.reshape(-1)
                
                # Only compute loss on valid (non-padding) tokens
                loss = torch.nn.functional.cross_entropy(
                    logits_flat[mask_flat],
                    targets_flat[mask_flat],
                    reduction='mean'
                )
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(lm.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            
            step += 1
            
            if step % 10 == 0:
                log.info(f"Step {step}/{MAX_STEPS} | Loss: {loss.item():.4f} | LR: {scheduler.get_last_lr()[0]:.6f}")
            
            if step % SAVE_EVERY == 0:
                ckpt_path = CHECKPOINT_DIR / f"step_{step:06d}.pt"
                torch.save({
                    "step": step,
                    "loss": loss.item(),
                    "lm_state_dict": lm.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                }, ckpt_path)
                log.info(f"Checkpoint saved: {ckpt_path}")
                
                if loss.item() < best_loss:
                    best_loss = loss.item()
                    best_path = CHECKPOINT_DIR / "best_model.pt"
                    torch.save(lm.state_dict(), best_path)
                    log.info(f"New best model! Loss: {best_loss:.4f}")
                    
        except Exception as e:
            log.error(f"Step {step} failed: {e}")
            step += 1
            continue
    
    # Final save
    final_path = CHECKPOINT_DIR / "final_model.pt"
    torch.save(lm.state_dict(), final_path)
    log.info("=" * 60)
    log.info(f"TRAINING COMPLETE! {MAX_STEPS} steps done.")
    log.info(f"Final model: {final_path}")
    log.info(f"Best model: {CHECKPOINT_DIR}/best_model.pt")
    log.info("=" * 60)

if __name__ == "__main__":
    main()
