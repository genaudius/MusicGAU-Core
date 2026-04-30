import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from musicgau.enrichment.audio_to_midi import MusicGAUAudioToMidi

def run_stem_to_midi_test():
    # Path to the bass stem generated in previous test
    bass_stem = r"outputs\separated_stems\htdemucs\01 Malo\bass.wav"
    
    if not os.path.exists(bass_stem):
        print(f"Error: Stem not found at {bass_stem}. Run separation first.")
        return

    transcriber = MusicGAUAudioToMidi(output_dir="outputs/processed_midi/transcriptions")
    midi_path = transcriber.transcribe(bass_stem)
    
    if midi_path:
        print("\n--- STEM TO MIDI SUCCESS ---")
        print(f"MIDI generated: {midi_path}")
    else:
        print("\n--- TRANSCRIPTION FAILED ---")

if __name__ == "__main__":
    run_stem_to_midi_test()
