import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from musicgau.enrichment.stem_separator import MusicGAUStemSeparator

def run_batch_separation():
    # Folder to process
    music_dir = r"I:\Users\subet\Music\Musica\CARPETA DE BACHATA\Danny Garcia"
    
    if not os.path.exists(music_dir):
        print(f"Error: Directory not found at {music_dir}")
        return

    separator = MusicGAUStemSeparator()
    
    # Get all mp3 files
    files = [f for f in os.listdir(music_dir) if f.lower().endswith(".mp3")]
    print(f"Found {len(files)} tracks in {music_dir}")
    
    # Process first 5 for now to avoid massive processing time in one go
    # but we can scale it.
    for f in files[:5]:
        full_path = os.path.join(music_dir, f)
        print(f"\n>>> Processing: {f}")
        try:
            separator.separate(full_path)
        except Exception as e:
            print(f"Error processing {f}: {e}")

if __name__ == "__main__":
    run_batch_separation()
