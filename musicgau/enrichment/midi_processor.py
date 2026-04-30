import os
import mido
import numpy as np
from pathlib import Path
from pedalboard import Pedalboard, Reverb, Chorus, Compressor, Gain
from pedalboard.io import AudioFile
import pyloudnorm as pyln
import soundfile as sf

class MusicGAUMidiProcessor:
    def __init__(self, output_dir: str = "outputs/processed_midi"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.meter = pyln.Meter(44100) # Standard 44.1kHz

    def split_midi_by_track(self, midi_path: str):
        """
        Splits a MIDI file into multiple MIDI files, one per track.
        """
        mid = mido.MidiFile(midi_path)
        midi_name = Path(midi_path).stem
        split_dir = self.output_dir / "splits" / midi_name
        split_dir.mkdir(parents=True, exist_ok=True)
        
        tracks = []
        for i, track in enumerate(mid.tracks):
            new_mid = mido.MidiFile()
            new_mid.ticks_per_beat = mid.ticks_per_beat
            new_mid.tracks.append(track)
            
            # Clean name for the track
            track_name = "".join([c if c.isalnum() else "_" for c in track.name]) or f"track_{i}"
            out_path = split_dir / f"{track_name}.mid"
            new_mid.save(out_path)
            tracks.append(out_path)
            
        return tracks

    def synthesize_track(self, audio_data: np.ndarray, sample_rate: int, vst_path: str = None):
        """
        Applies Pedalboard effects to audio data.
        Note: Actual MIDI-to-Audio synthesis usually requires a VST instrument plugin 
        which Pedalboard can host.
        """
        board = Pedalboard([
            Compressor(threshold_db=-12, ratio=4),
            Gain(gain_db=2),
            Reverb(room_size=0.25),
        ])
        
        # If a VST path is provided, we could load it here (requires pedalboard.VST3Plugin)
        # However, for now we apply a standard production chain.
        effected = board(audio_data, sample_rate)
        return effected

    def normalize_audio(self, audio_data: np.ndarray, sample_rate: int, target_lufs: float = -14.0):
        """
        Normalizes audio to a target LUFS using pyloudnorm.
        """
        # Measure loudness
        loudness = self.meter.measure(audio_data)
        
        # Shift loudness to target
        normalized_audio = pyln.normalize.loudness(audio_data, loudness, target_lufs)
        
        # Peak normalization to 1.0 (0 dBFS)
        peak = np.max(np.abs(normalized_audio))
        if peak > 0:
            normalized_audio = normalized_audio / peak
            
        return normalized_audio

    def process_full_pipeline(self, midi_path: str, dummy_audio_source: str = None):
        """
        Example pipeline: Split MIDI -> (Synthesize) -> Normalize -> Save
        """
        print(f"Processing {midi_path}...")
        midi_splits = self.split_midi_by_track(midi_path)
        print(f"Split into {len(midi_splits)} tracks.")
        
        # Since we don't have the VSTs yet to turn MIDI to Audio, 
        # we'll assume we have a WAV source for testing the production chain.
        if dummy_audio_source and os.path.exists(dummy_audio_source):
            with AudioFile(dummy_audio_source) as f:
                audio = f.read(f.frames)
                sr = f.samplerate
                
            # Production Chain
            processed = self.synthesize_track(audio, sr)
            
            # Normalization
            normalized = self.normalize_audio(processed, sr)
            
            out_wav = self.output_dir / f"{Path(midi_path).stem}_final.wav"
            with AudioFile(str(out_wav), 'w', sr, normalized.shape[0]) as f:
                f.write(normalized)
            print(f"Saved processed audio to {out_wav}")

if __name__ == "__main__":
    processor = MusicGAUMidiProcessor()
    # Test with a sample MIDI if available
    # processor.process_full_pipeline("path/to/midi.mid")
