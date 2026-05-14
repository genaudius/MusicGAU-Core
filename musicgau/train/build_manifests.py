import os
import json
import gzip
from pathlib import Path
import librosa
from tqdm import tqdm

# --- Configuration ---
DATASET_ROOT = Path("datasets/bachata_stems_v1")
TRAIN_DIR = DATASET_ROOT / "train"
MANIFEST_DIR = DATASET_ROOT / "manifests"
OUTPUT_FILE = MANIFEST_DIR / "train.jsonl.gz"
SAMPLE_RATE = 32000  # AudioCraft default

def build_manifests():
    print(f"--- Building AudioCraft Manifests in {DATASET_ROOT} ---")
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    
    entries = []
    
    # Iterate over all audio files in the train directory
    # We expect structure: train/<song_name>/<stem_type>/<chunk>.wav
    audio_files = list(TRAIN_DIR.rglob("*.wav"))
    print(f"Found {len(audio_files)} audio files.")
    
    for audio_path in tqdm(audio_files, desc="Processing audio"):
        try:
            # Get relative path from DATASET_ROOT for the manifest
            rel_path = str(audio_path.relative_to(DATASET_ROOT)).replace("\\", "/")
            
            # Load metadata
            duration = librosa.get_duration(path=audio_path)
            
            # Determine prompt based on directory structure
            # e.g., train/nadie_muere/guira/chunk.wav -> "bachata, guira, nadie muere"
            parts = audio_path.relative_to(TRAIN_DIR).parts
            song_name = parts[0].replace("_", " ")
            stem_type = parts[1] if len(parts) > 1 else "mixdown"
            
            prompt = f"bachata, {stem_type}, {song_name}"
            
            entry = {
                "path": str(audio_path.absolute()),
                "duration": duration,
                "sample_rate": SAMPLE_RATE,
                "amplitude": 1.0,
                "description": prompt,
                "genre": "bachata",
                "instrument": stem_type
            }
            entries.append(entry)
            
        except Exception as e:
            print(f"Error processing {audio_path}: {e}")

    # Write to gzipped jsonl
    print(f"Writing {len(entries)} entries to {OUTPUT_FILE}...")
    with gzip.open(OUTPUT_FILE, "wt", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
            
    # Also create a small validation set (last 5% of entries)
    valid_file = MANIFEST_DIR / "valid.jsonl.gz"
    valid_count = max(1, int(len(entries) * 0.05))
    valid_entries = entries[-valid_count:]
    
    with gzip.open(valid_file, "wt", encoding="utf-8") as f:
        for entry in valid_entries:
            f.write(json.dumps(entry) + "\n")

    print(f"Manifests created successfully! ✅")

if __name__ == "__main__":
    build_manifests()
