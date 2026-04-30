import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from musicgau.enrichment.metadata.spotify_client import MusicGAUSpotifyClient
from musicgau.enrichment.metadata.lastfm_client import MusicGAULastFMClient
from musicgau.engine.prompter import ChatGAU

class MusicGAUBatchProcessor:
    def __init__(self, output_dir: str = "outputs/training_manifests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.sp = MusicGAUSpotifyClient()
        self.lfm = MusicGAULastFMClient()
        self.chatgau = ChatGAU()

    def process_file(self, artist: str, track_name: str, midi_path: str):
        print(f"\n>>> Processing: {artist} - {track_name}")
        
        # 1. Fetch metadata
        sp_data = self.sp.get_full_enrichment(track_name, artist)
        tags = self.lfm.get_contextual_tags(artist, track_name)
        
        if not sp_data:
            sp_data = {
                "info": {"name": track_name, "artist": artist, "genre": "Tropical"},
                "features": {"energy": 0.7, "tempo": 125},
                "sections": []
            }

        # 2. Consolidate
        full_meta = {
            "info": sp_data["info"],
            "features": sp_data["features"],
            "tags": tags,
            "midi_source": str(midi_path),
            "patch": {"add": ["tropical percussion", "live brass"]}
        }

        # 3. Generate Prompt
        full_meta["prompt"] = self.chatgau.humanize_json(full_meta)
        
        # 4. Save manifest
        safe_name = f"{artist}_{track_name}".replace(" ", "_").replace(".", "")
        out_file = self.output_dir / f"{safe_name}.json"
        
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(full_meta, f, indent=2, ensure_ascii=False)
            
        print(f"Saved: {out_file}")
        return out_file

    def run_batch(self, tracks):
        results = []
        for track in tracks:
            res = self.process_file(track["artist"], track["track"], track["path"])
            results.append(res)
        return results

if __name__ == "__main__":
    processor = MusicGAUBatchProcessor()
    
    # Define tropical batch
    root = r"C:\Users\genau\GenAudiu_AI\data\clean_midi\clean_midi"
    tropical_batch = [
        {"artist": "Juan Luis Guerra", "track": "Como abeja al panal", "path": os.path.join(root, "Juan Luis Guerra", "Como abeja al panal.mid")},
        {"artist": "Juan Luis Guerra", "track": "La Bilirrubina", "path": os.path.join(root, "Juan Luis Guerra", "La Bilirrubina.mid")},
        {"artist": "Marc Anthony", "track": "Hasta Ayer", "path": os.path.join(root, "Marc Anthony", "Hasta Ayer.mid")},
        {"artist": "Marc Anthony", "track": "Vivir Lo Nuestro", "path": os.path.join(root, "Marc Anthony", "Vivir Lo Nuestro.mid")},
    ]
    
    processor.run_batch(tropical_batch)
