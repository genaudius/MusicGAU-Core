import os
import runpod
from pathlib import Path
from musicgau.train.run_audiocraft import train as run_train

def handler(job):
    """
    RunPod Serverless handler for MusicGAU training.
    Expected input:
    {
        "input": {
            "dataset_root": "datasets/bachata_stems_v1",
            "out_dir": "checkpoints/musicgau_bachata",
            "max_steps": 5000,
            "batch_size": 4,
            "lr": 1e-4,
            "dry_run": false,
            "solver_config": "musicgen/musicgen_base_32khz"
        }
    }
    """
    job_input = job.get('input', {})
    
    # Extract parameters with sensible defaults from the CLI script
    dataset_root = Path(job_input.get('dataset_root', 'datasets/bachata_stems_v1'))
    out_dir = Path(job_input.get('out_dir', 'checkpoints/musicgau_bachata'))
    max_steps = int(job_input.get('max_steps', 5000))
    batch_size = int(job_input.get('batch_size', 4))
    lr = float(job_input.get('lr', 1e-4))
    dry_run = bool(job_input.get('dry_run', False))
    solver_config = job_input.get('solver_config', 'musicgen/musicgen_base_32khz')
    
    # Set environment variables if needed (AudioCraft/Dora often use USER)
    if "USER" not in os.environ:
        os.environ["USER"] = "runpod"

    print(f"--- Starting Training Job ---")
    print(f"Dataset Root: {dataset_root}")
    print(f"Output Dir: {out_dir}")
    print(f"Max Steps: {max_steps}")
    print(f"Batch Size: {batch_size}")
    
    try:
        # We call the train function directly. 
        # Note: Typer functions can be called directly, but we need to pass all expected arguments
        # if they don't have defaults in the function signature that we want to keep.
        run_train(
            dataset_root=dataset_root,
            out_dir=out_dir,
            solver_config=solver_config,
            max_steps=max_steps,
            batch_size=batch_size,
            lr=lr,
            dry_run=dry_run,
            device="cuda" # Force CUDA on RunPod
        )
        
        return {
            "status": "success",
            "message": f"Training completed for {max_steps} steps.",
            "output_dir": str(out_dir)
        }
    except Exception as e:
        print(f"Error during training: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
