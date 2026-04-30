import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from musicgau.enrichment.midi_processor import MusicGAUMidiProcessor

def run_batch_split():
    processor = MusicGAUMidiProcessor(output_dir="outputs/processed_midi")
    
    root = r"C:\Users\genau\GenAudiu_AI\data\clean_midi\clean_midi"
    tropical_batch = [
        {"artist": "Juan Luis Guerra", "track": "Como abeja al panal", "path": os.path.join(root, "Juan Luis Guerra", "Como abeja al panal.mid")},
        {"artist": "Juan Luis Guerra", "track": "La Bilirrubina", "path": os.path.join(root, "Juan Luis Guerra", "La Bilirrubina.mid")},
        {"artist": "Marc Anthony", "track": "Hasta Ayer", "path": os.path.join(root, "Marc Anthony", "Hasta Ayer.mid")},
        {"artist": "Marc Anthony", "track": "Vivir Lo Nuestro", "path": os.path.join(root, "Marc Anthony", "Vivir Lo Nuestro.mid")},
    ]
    
    print("--- MusicGAU Batch MIDI Splitter ---")
    
    for item in tropical_batch:
        print(f"\nSplitting: {item['artist']} - {item['track']}")
        try:
            # Use artist_track name for the folder
            safe_name = f"{item['artist']}_{item['track']}".replace(" ", "_")
            # We override the output logic slightly to keep it organized
            midi_splits = processor.split_midi_by_track(item['path'])
            print(f"Successfully split into {len(midi_splits)} instrument tracks.")
            for s in midi_splits:
                print(f"  - {s.name}")
        except Exception as e:
            print(f"Error splitting {item['track']}: {e}")

if __name__ == "__main__":
    run_batch_split()
