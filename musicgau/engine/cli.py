from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from musicgau import MODEL_NAME
from musicgau.config import get_paths
from musicgau.engine.generator import GenerateRequest, generate_to_wav


app = typer.Typer(add_completion=False, help=f"{MODEL_NAME} engine CLI")
console = Console()


@app.command()
def info() -> None:
    p = get_paths()
    payload = {
        "model_name": MODEL_NAME,
        "repo_root": str(p.repo_root),
        "data_dir": str(p.data_dir),
        "cache_dir": str(p.cache_dir),
        "outputs_dir": str(p.outputs_dir),
        "checkpoints_dir": str(p.checkpoints_dir),
    }
    console.print_json(json.dumps(payload))


@app.command()
def generate(
    prompt: str = typer.Option(..., help="Text prompt describing the desired audio."),
    genre: str = typer.Option("salsa", help="Genre preset key."),
    bpm: Optional[float] = typer.Option(None, help="Target BPM (optional)."),
    key: Optional[str] = typer.Option(None, help="Musical key (e.g., Am, C)."),
    seconds: int = typer.Option(30, help="Duration in seconds."),
    seed: int = typer.Option(42, help="Random seed."),
    out: Path = typer.Option(Path("outputs/out.wav"), help="Output WAV path."),
    base_model: str = typer.Option("facebook/musicgen-small", help="Base MusicGen model name or path."),
) -> None:
    req = GenerateRequest(
        prompt=prompt,
        genre=genre,
        bpm=bpm,
        key=key,
        seconds=seconds,
        seed=seed,
        base_model=base_model,
    )
    meta = generate_to_wav(req, out)
    console.print_json(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    app()

