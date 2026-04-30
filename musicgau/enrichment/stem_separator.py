import os
import subprocess
from pathlib import Path
from typing import Dict, List

class MusicGAUStemSeparator:
    def __init__(self, model: str = "htdemucs", output_dir: str = "outputs/separated_stems"):
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def separate(self, audio_path: str) -> Dict[str, str]:
        """
        Separates an audio file into vocals, drums, bass, and other.
        Uses Demucs via CLI for stability.
        """
        # Add FFmpeg to path if found in Pinokio or other common spots
        ffmpeg_dir = r"C:\pinokio\bin\ffmpeg-env\Library\bin"
        if os.path.exists(ffmpeg_dir) and ffmpeg_dir not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + ffmpeg_dir

        print(f"Separating stems for: {audio_path}")
        audio_file = Path(audio_path)
        
        # Demucs command
        # -n: model name
        # -o: output directory
        command = [
            "demucs",
            "-n", self.model,
            "-o", str(self.output_dir),
            audio_path
        ]
        
        try:
            subprocess.run(command, check=True)
            
            # Locate output files
            # Demucs creates a folder: output_dir/model/filename_stem/
            stem_dir = self.output_dir / self.model / audio_file.stem
            
            stems = {
                "vocals": str(stem_dir / "vocals.wav"),
                "drums": str(stem_dir / "drums.wav"),
                "bass": str(stem_dir / "bass.wav"),
                "other": str(stem_dir / "other.wav")
            }
            
            # Verify they exist
            found_stems = {k: v for k, v in stems.items() if os.path.exists(v)}
            print(f"Separation complete. Stems found: {list(found_stems.keys())}")
            return found_stems
            
        except Exception as e:
            print(f"Error during separation: {e}")
            return {}

if __name__ == "__main__":
    # Test with a dummy or real file
    separator = MusicGAUStemSeparator()
    # separator.separate("path/to/audio.wav")
