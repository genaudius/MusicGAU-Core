import os
import subprocess
from pathlib import Path

class MusicGAUAudioToMidi:
    def __init__(self, output_dir: str = "outputs/audio_to_midi"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def transcribe(self, audio_path: str) -> str:
        """
        Transcribes audio to MIDI using Spotify's Basic Pitch.
        """
        print(f"Transcribing audio to MIDI: {audio_path}")
        
        # basic-pitch <output_directory> <input_audio_path>
        command = [
            "basic-pitch",
            str(self.output_dir),
            audio_path
        ]
        
        # Add UTF-8 encoding to environment to handle emojis in basic-pitch output
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        try:
            subprocess.run(command, check=True, env=env)
            
            # Basic Pitch saves as filename_basic_pitch.mid
            audio_file = Path(audio_path)
            midi_path = self.output_dir / f"{audio_file.stem}_basic_pitch.mid"
            
            if midi_path.exists():
                print(f"Transcription complete: {midi_path}")
                return str(midi_path)
            return ""
            
        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""

if __name__ == "__main__":
    transcriber = MusicGAUAudioToMidi()
    # transcriber.transcribe("path/to/audio.wav")
