import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from musicgau.enrichment.stem_separator import MusicGAUStemSeparator

def run_test_separation():
    # File to test
    audio_path = r"I:\Users\subet\Music\Musica\CARPETA DE BACHATA\Danny Garcia\01 Malo.mp3"
    
    if not Path(audio_path).exists():
        print(f"Error: File not found at {audio_path}")
        return

    separator = MusicGAUStemSeparator()
    stems = separator.separate(audio_path)
    
    if stems:
        print("\n--- TEST SUCCESSFUL ---")
        print("Generated Stems:")
        for name, path in stems.items():
            print(f"  - {name}: {path}")
    else:
        print("\n--- TEST FAILED ---")

if __name__ == "__main__":
    run_test_separation()
