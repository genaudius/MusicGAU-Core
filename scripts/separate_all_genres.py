import os
import subprocess
from pathlib import Path

base_raw = Path("/workspace/GenAudius_V1/datasets/incoming_raw")
output_base = Path("/workspace/GenAudius_V1/datasets/stems_extracted")

# Dynamically find all genre folders
genres = [d.name for d in base_raw.iterdir() if d.is_dir()]

print(f"Detected genres: {genres}")

for genre in genres:
    genre_path = base_raw / genre
    print(f"--- Processing {genre.upper()} ---")
    
    # Process both mp3, wma and any other audio files
    files = []
    for ext in ["*.mp3", "*.wma", "*.wav", "*.m4a"]:
        files.extend(list(genre_path.glob(ext)))
        files.extend(list(genre_path.glob(ext.upper())))
    
    print(f"Found {len(files)} tracks in {genre}")
    
    for audio_file in files:
        # Check if already processed (check if folder exists in output)
        song_name = audio_file.stem
        if (output_base / "htdemucs" / song_name).exists():
            print(f"  Skipping {audio_file.name} (already processed)")
            continue
            
        print(f"  Separating: {audio_file.name}")
        cmd = [
            "demucs",
            "-n", "htdemucs",
            "--out", str(output_base),
            str(audio_file)
        ]
        try:
            subprocess.run(cmd, check=True)
        except Exception as e:
            print(f"  Error processing {audio_file.name}: {e}")

print("All detected genres separated! ✅")
