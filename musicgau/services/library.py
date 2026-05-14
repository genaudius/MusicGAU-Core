import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class MusicGAULibraryService:
    def __init__(self, library_file: str = "outputs/generated_library.jsonl"):
        self.library_path = Path(library_file)
        self.library_path.parent.mkdir(parents=True, exist_ok=True)

    def catalog_track(self, 
                      track_path: str, 
                      prompt: str, 
                      metadata: Optional[Dict[str, Any]] = None,
                      tags: Optional[list] = None):
        """
        Adds a generated track to the professional catalog.
        """
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "audio_path": str(Path(track_path).absolute()),
            "prompt": prompt,
            "metadata": metadata or {},
            "tags": tags or [],
            "status": "production_ready"
        }
        
        with open(self.library_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
        print(f"[Library] Track cataloged: {Path(track_path).name}")
        return entry

    def get_recent_tracks(self, limit: int = 10):
        """
        Retrieves recent entries from the catalog.
        """
        if not self.library_path.exists():
            return []
            
        tracks = []
        with open(self.library_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tracks.append(json.loads(line))
        
        return tracks[-limit:]

if __name__ == "__main__":
    lib = MusicGAULibraryService()
    # lib.catalog_track("test.mp3", "A test bachata track")
    print(f"Current library has {len(lib.get_recent_tracks(100))} tracks.")
