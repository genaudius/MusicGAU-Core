from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console


app = typer.Typer(add_completion=False, help="Wrapper to run AudioCraft MusicGen LoRA training for MusicGAU.")
console = Console()


@app.command()
def run(
    dataset_root: Path = typer.Option(..., exists=True, file_okay=False, help="Folder with manifests/ and audio clips."),
    exp_dir: Path = typer.Option(Path("checkpoints/musicgau"), help="Where to write checkpoints/logs."),
    base_model: str = typer.Option("facebook/musicgen-small", help="Base MusicGen model name or path."),
    max_steps: int = typer.Option(5000, help="Training steps (adjust to dataset size)."),
    batch_size: int = typer.Option(4, help="Batch size per GPU."),
    lr: float = typer.Option(1e-4, help="Learning rate."),
) -> None:
    exp_dir.mkdir(parents=True, exist_ok=True)

    train_manifest = dataset_root / "manifests" / "train.jsonl.gz"
    valid_manifest = dataset_root / "manifests" / "valid.jsonl.gz"
    if not train_manifest.exists():
        train_manifest = dataset_root / "manifests" / "train.jsonl"
    if not valid_manifest.exists():
        valid_manifest = dataset_root / "manifests" / "valid.jsonl"

    console.print("[bold]MusicGAU Training (AudioCraft + LoRA)[/bold]")
    console.print(f"- dataset_root: {dataset_root}")
    console.print(f"- train_manifest: {train_manifest}")
    console.print(f"- valid_manifest: {valid_manifest}")
    console.print(f"- exp_dir: {exp_dir}")
    console.print(f"- base_model: {base_model}")
    console.print(f"- max_steps: {max_steps}, batch_size: {batch_size}, lr: {lr}")

    env = {
        "MUSICGAU_DATASET_ROOT": str(dataset_root),
        "MUSICGAU_EXP_DIR": str(exp_dir),
    }
    for k, v in env.items():
        os.environ[k] = v

    console.print("\nNext step: configure AudioCraft training configs in `musicgau/train/configs/`.")
    console.print("We'll wire manifests into Hydra config and enable LoRA on the LM modules.")


if __name__ == "__main__":
    app()

