import os
import shutil
from pathlib import Path

source_dir = Path("/workspace/GenAudius_V1/datasets/stems_extracted/htdemucs")
dest_base = Path("/workspace/GenAudius_V1/datasets/bachata_stems_v1/train/danny_garcia_protegido")

if not source_dir.exists():
    print(f"Source dir {source_dir} not found!")
    exit(1)

for song_folder in source_dir.iterdir():
    if not song_folder.is_dir():
        continue
    
    song_name = song_folder.name
    print(f"Processing {song_name}...")
    
    mapping = {
        "drums.wav": "percusion",
        "bass.wav": "bajo",
        "other.wav": "guitarras",
        "vocals.wav": "voces"
    }
    
    for src_file, target_stem in mapping.items():
        src_path = song_folder / src_file
        if src_path.exists():
            target_dir = dest_base / song_name / target_stem
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Use song name in the final filename
            target_file = target_dir / f"{song_name}_{target_stem}.wav"
            shutil.move(str(src_path), str(target_file))
            print(f"  Moved {src_file} to {target_stem}")

print("Done organizing stems! ✅")
