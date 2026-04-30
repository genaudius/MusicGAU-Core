from __future__ import annotations

import json
import time
from pathlib import Path

import torch
import typer
from rich.console import Console


app = typer.Typer(add_completion=False, help="Run Masculine + Feminine + Dueto (in order) and write outputs under models/.")
console = Console()


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _write_placeholder_pth(path: Path, *, speaker: str, name: str) -> None:
    _ensure_dir(path.parent)
    ckpt = {
        "placeholder": True,
        "created_at_unix": int(time.time()),
        "meta": {"model_type": "placeholder", "speaker": speaker, "name": name},
        "state_dict": {},
    }
    torch.save(ckpt, path)


def _write_outputs(model_dir: Path, *, speaker: str, checkpoint_name: str) -> None:
    """
    Materialize a stable outputs layout expected by downstream tooling:
    - model_dir/dataset/          (input dataset placeholder)
    - model_dir/<checkpoint>.pth  (checkpoint placeholder or trained model)
    - model_dir/outputs/          (generated artifacts)
    - model_dir/outputs/run_meta.json
    """
    _ensure_dir(model_dir / "dataset")
    _ensure_dir(model_dir / "outputs")

    ckpt_path = model_dir / checkpoint_name
    if not ckpt_path.exists():
        _write_placeholder_pth(ckpt_path, speaker=speaker, name=ckpt_path.stem)

    meta = {
        "speaker": speaker,
        "checkpoint": str(ckpt_path).replace("\\", "/"),
        "dataset_dir": str((model_dir / "dataset").resolve()).replace("\\", "/"),
        "outputs_dir": str((model_dir / "outputs").resolve()).replace("\\", "/"),
        "status": "ok",
        "note": "Placeholder outputs (add real dataset/manifests + training to replace checkpoints).",
        "created_at_unix": int(time.time()),
    }
    (model_dir / "outputs" / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


@app.command()
def run(
    models_root: Path = typer.Option(Path("models"), help="Root containing masculine/feminine/dueto folders."),
) -> None:
    """
    Runs Masculine -> Feminine -> Dueto and leaves outputs under:
      models/masculine/, models/feminine/, models/dueto/
    """
    trio = [
        ("masculine", "danny_v1.pth"),
        ("feminine", "vocal_female_1.pth"),
        ("dueto", "dueto_v1.pth"),
    ]

    models_root = models_root.resolve()
    console.print(f"[bold]Voice trio run[/bold] models_root={models_root}")
    for speaker, ckpt in trio:
        model_dir = models_root / speaker
        console.print(f"- {speaker} -> {model_dir}")
        _write_outputs(model_dir, speaker=speaker, checkpoint_name=ckpt)

    console.print("[green]Done.[/green]")


if __name__ == "__main__":
    app()

