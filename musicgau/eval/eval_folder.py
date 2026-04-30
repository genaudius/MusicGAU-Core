from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from tqdm import tqdm

from musicgau.eval.audio_checks import run_basic_checks


app = typer.Typer(add_completion=False, help="Run basic QC checks over a folder of WAVs.")
console = Console()


@app.command()
def run(
    folder: Path = typer.Option(Path("outputs"), help="Folder to scan for .wav files."),
    out_json: Path = typer.Option(Path("outputs/eval_basic_checks.json"), help="Where to write results JSON."),
) -> None:
    wavs = sorted([p for p in folder.rglob("*.wav") if p.is_file()])
    if not wavs:
        raise typer.BadParameter(f"No .wav files found under: {folder}")

    results = []
    for p in tqdm(wavs, desc="checks"):
        try:
            results.append(run_basic_checks(p).__dict__)
        except Exception as e:
            results.append({"path": str(p), "error": str(e)})

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    console.print(f"Wrote {out_json} ({len(results)} files)")


if __name__ == "__main__":
    app()

