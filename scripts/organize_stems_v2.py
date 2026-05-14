import os
import shutil
from pathlib import Path

source_base = Path("/workspace/GenAudius_V1/datasets/stems_extracted/htdemucs")
dest_base_root = Path("/workspace/GenAudius_V1/datasets/bachata_stems_v1/train")

# Mapping of genres to their folder names in the training set
# We will use the same folder name as the raw source for simplicity
if not source_base.exists():
    print(f"Source base {source_base} not found!")
    exit(1)

for song_folder in source_base.iterdir():
    if not song_folder.is_dir():
        continue
    
    song_name = song_folder.name
    
    # We need to find which genre this song belongs to
    # We'll check the incoming_raw folders
    raw_base = Path("/workspace/GenAudius_V1/datasets/incoming_raw")
    genre_found = "unknown"
    for genre_dir in raw_base.iterdir():
        if not genre_dir.is_dir(): continue
        # Check if original file existed in this genre dir
        if any(genre_dir.glob(f"{song_name}.*")):
            genre_found = genre_dir.name
            break
            
    print(f"Processing {song_name} (Genre: {genre_found})...")
    
    dest_path = dest_base_root / genre_found / song_name
    
    mapping = {
        "drums.wav": "percusion",
        "bass.wav": "bajo",
        "other.wav": "instrumental",
        "vocals.wav": "voces"
    }
    
    for src_file, target_stem in mapping.items():
        src_path = song_folder / src_file
        if src_path.exists():
            target_dir = dest_path / target_stem
            target_dir.mkdir(parents=True, exist_ok=True)
            
            target_file = target_dir / f"{song_name}_{target_stem}.wav"
            # Overwrite if exists
            if target_file.exists():
                os.remove(target_file)
            shutil.move(str(src_path), str(target_file))
            print(f"  Moved {src_file} to {genre_found}/{target_stem}")

print("Done organizing all stems! ✅")
