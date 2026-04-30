import os
import runpod
from pathlib import Path
from musicgau.enrichment.stem_separator import MusicGAUStemSeparator
from musicgau.enrichment.audio_to_midi import MusicGAUAudioToMidi
# Assume training is still there
try:
    from musicgau.train.run_audiocraft import train as run_train
except ImportError:
    run_train = None

def handler(job):
    """
    GenAudius Unified Serverless Handler.
    Supports: 
    - "task": "generate"
    - "task": "separate"
    - "task": "midi"
    - "task": "train"
    """
    job_input = job.get('input', {})
    
    # --- Security Shield ---
    api_key = job_input.get('api_key')
    expected_key = os.getenv("GAU_API_KEY", "gau_master_secure_2026")
    if api_key != expected_key:
        return {"error": "Unauthorized: Invalid or missing API Key"}
    
    task = job_input.get('task', 'generate')
    
    print(f"--- MusicGAU Engine: Processing Task [{task}] ---")

    if task == "separate":
        # Input: {"task": "separate", "audio_url": "http://..."}
        audio_url = job_input.get('audio_url')
        if not audio_url:
            return {"error": "Missing audio_url"}
        
        # Download file (RunPod often needs to fetch from external or storage)
        # For simplicity, we assume the path is local or pre-downloaded
        # Or we use requests to fetch it
        import requests
        local_path = Path("/tmp") / f"input_{job['id']}.wav"
        r = requests.get(audio_url)
        with open(local_path, 'wb') as f:
            f.write(r.content)
            
        separator = MusicGAUStemSeparator()
        stems = separator.separate(str(local_path))
        return {"status": "success", "data": stems}

    elif task == "midi":
        # Input: {"task": "midi", "audio_url": "http://..."}
        audio_url = job_input.get('audio_url')
        if not audio_url:
            return {"error": "Missing audio_url"}
            
        import requests
        local_path = Path("/tmp") / f"input_midi_{job['id']}.wav"
        r = requests.get(audio_url)
        with open(local_path, 'wb') as f:
            f.write(r.content)
            
        transcriber = MusicGAUAudioToMidi()
        midi_path = transcriber.transcribe(str(local_path))
        return {"status": "success", "data": {"midi_url": midi_path}}

    elif task == "train":
        if not run_train:
            return {"error": "Training module not found in this image"}
        # Existing training logic...
        # 1. Pre-build manifests to include any new audio files
        import subprocess
        try:
            print("--- Rebuilding manifests ---")
            subprocess.run(["python", "musicgau/train/build_manifests.py"], check=True)
        except Exception as e:
            print(f"Warning: Manifest rebuild failed: {e}")

        dataset_root = Path(job_input.get('dataset_root', 'datasets/bachata_stems_v1'))
        out_dir = Path(job_input.get('out_dir', f"checkpoints/{job['id']}"))
        max_steps = int(job_input.get('max_steps', 5000))
        
        run_train(
            dataset_root=dataset_root,
            out_dir=out_dir,
            max_steps=max_steps,
            device="cuda"
        )
        return {"status": "success", "out_dir": str(out_dir)}

    else:
        return {"error": f"Unknown task type: {task}"}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
