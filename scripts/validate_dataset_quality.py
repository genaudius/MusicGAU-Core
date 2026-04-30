"""
MusicGAU Dataset Quality Validator
Este script verifica que tus archivos de audio cumplan con los estándares
de "Alta Fidelidad" requeridos para el entrenamiento profesional.
"""

import sys
from pathlib import Path
import soundfile as sf
import numpy as np

try:
    import pyloudnorm as pyln
    HAS_PYLOUDNORM = True
except ImportError:
    HAS_PYLOUDNORM = False

def validate_audio(file_path: Path):
    print(f"\n--- Analizando: {file_path.name} ---")
    
    try:
        data, sr = sf.read(file_path)
    except Exception as e:
        print(f"❌ ERROR: No se pudo leer el archivo. {e}")
        return

    # 1. Sample Rate
    if sr < 32000:
        print(f"ALERTA CALIDAD: Sample rate bajo ({sr}Hz). Se recomienda 32000Hz o 44100Hz.")
    else:
        print(f"OK - Sample Rate: {sr}Hz")

    # 2. Canales
    channels = data.shape[1] if len(data.shape) > 1 else 1
    if channels < 2:
        print(f"ALERTA CANALES: El archivo es Mono. Para máxima fidelidad se prefiere Estéreo.")
    else:
        print(f"OK - Canales: {channels} (Estéreo)")

    # 3. Duración
    duration = len(data) / sr
    if duration < 30.0:
        print(f"ALERTA DURACIÓN: {duration:.2f}s. Los clips de menos de 30s pueden ser menos efectivos.")
    else:
        print(f"OK - Duración: {duration:.2f}s")

    # 4. Loudness (LUFS)
    if HAS_PYLOUDNORM:
        meter = pyln.Meter(sr)
        try:
            loudness = meter.integrated_loudness(data)
            print(f"INFO - Loudness: {loudness:.2f} LUFS")
            if abs(loudness - (-14.0)) > 2.0:
                print(f"ALERTA NIVEL: Se recomienda normalizar a -14 LUFS (actual: {loudness:.2f})")
            else:
                print(f"OK - Nivel: {loudness:.2f} LUFS (Excelente)")
        except Exception:
            print("ALERTA LOUDNESS: Error al calcular. Asegúrate de que el audio no tenga silencios largos.")
    else:
        print("INFO - NOTA: Instala 'pyloudnorm' para verificar el nivel exacto de LUFS.")

def main(directory: str):
    root = Path(directory)
    if not root.exists():
        print(f"Error: El directorio {directory} no existe.")
        return

    audio_extensions = {".wav", ".flac", ".mp3"}
    files = [p for p in root.rglob("*") if p.suffix.lower() in audio_extensions]

    if not files:
        print("No se encontraron archivos de audio.")
        return

    print(f"Validando {len(files)} archivos...")
    for f in files[:10]: # Validamos los primeros 10 como muestra
        validate_audio(f)
    
    if len(files) > 10:
        print(f"\n... y {len(files) - 10} archivos más.")

if __name__ == "__main__":
    # Puedes pasar la ruta de tu carpeta de audios aquí
    path_to_check = r"C:\Users\genau\OneDrive\Desktop\Stems" 
    main(path_to_check)
