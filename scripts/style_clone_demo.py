"""
Style Cloning Demo - MusicGAU
Este script demuestra cómo usar MusicGen en modo 'melody' para replicar el estilo 
y la estructura rítmica de una bachata de referencia.
"""

from pathlib import Path
import torch
import soundfile as sf
from audiocraft.models import MusicGen

def clone_style(reference_wav: str, prompt: str, output_path: str, duration: int = 30):
    print(f"Cargando modelo MusicGen Melody (para In-Context Learning)...")
    # El modelo 'melody' permite usar un audio de referencia para guiar la estructura.
    model = MusicGen.get_pretrained('facebook/musicgen-melody')
    model.set_generation_params(duration=duration)

    print(f"Cargando audio de referencia: {reference_wav}")
    # Leemos la bachata original que queremos replicar
    melody_wav, sr = sf.read(reference_wav)
    melody_wav = torch.from_numpy(melody_wav).float().t().unsqueeze(0) # [B, C, T]
    
    if melody_wav.shape[1] > 2: # Si es multi-canal, bajamos a estéreo
        melody_wav = melody_wav[:, :2, :]

    print(f"Generando nueva bachata basada en el ADN de la referencia...")
    # El modelo generará una nueva pieza que sigue la 'melody' (ritmo/melodía) de la referencia
    # pero usando el estilo descrito en el prompt.
    output = model.generate_with_chroma(
        descriptions=[prompt],
        melody_wavs=melody_wav,
        melody_sample_rate=sr,
        progress=True
    )

    print(f"Guardando resultado en {output_path}")
    wav_np = output[0].detach().cpu().numpy().T
    sf.write(output_path, wav_np, model.sample_rate)
    print("¡Generación completada!")

if __name__ == "__main__":
    # Ejemplo de uso:
    # clone_style(
    #     reference_wav="data/referencias/bachata_clasica.wav",
    #     prompt="Bachata moderna, estilo urbano, requinto cristalino, bajo con mucho cuerpo, 125 BPM",
    #     output_path="outputs/clonacion_estilo_1.wav"
    # )
    print("Script de demostración de Clonación de Estilo cargado.")
    print("Usa la función clone_style() pasando tu bachata de referencia.")
