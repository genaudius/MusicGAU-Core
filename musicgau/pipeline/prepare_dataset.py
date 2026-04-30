from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from tqdm import tqdm

from musicgau.pipeline.audio import TARGET_SR, load_audio_stereo, lufs_normalize, slice_clips, write_wav
from musicgau.pipeline.manifest import clipmeta_to_audiocraft_row, write_jsonl
from musicgau.pipeline.schema import ClipMeta, build_description


app = typer.Typer(add_completion=False, help="Prepare WAV clips + JSONL manifests for AudioCraft.")
console = Console()


@dataclass(frozen=True)
class SplitSpec:
    train: float = 0.98
    valid: float = 0.01
    test: float = 0.01


def _list_audio_files(root: Path) -> list[Path]:
    exts = {".wav", ".flac", ".mp3", ".ogg", ".m4a"}
    files: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    files.sort()
    return files


def _assign_split(rng: random.Random, spec: SplitSpec) -> str:
    x = rng.random()
    if x < spec.train:
        return "train"
    if x < spec.train + spec.valid:
        return "valid"
    return "test"


@app.command()
def run(
    input_dir: Path = typer.Option(..., exists=True, file_okay=False, help="Root folder of your masters (and/or stems)."),
    output_dir: Path = typer.Option(Path("datasets/musicgau_clips"), help="Where to write normalized clips."),
    clip_seconds: float = typer.Option(30.0, help="Clip duration in seconds."),
    hop_seconds: float = typer.Option(15.0, help="Hop duration in seconds (overlap allowed)."),
    target_lufs: float = typer.Option(-14.0, help="Target LUFS normalization."),
    seed: int = typer.Option(1234, help="Seed for split assignment."),
    gzip_manifest: bool = typer.Option(True, help="Write manifests as .jsonl.gz"),
    default_genre: Optional[str] = typer.Option("Bachata", help="Fallback genre."),
) -> None:
    """
    Creates normalized clips and manifests with rich metadata.
    """
    rng = random.Random(seed)
    spec = SplitSpec()

    audio_files = _list_audio_files(input_dir)
    if not audio_files:
        raise typer.BadParameter(f"No audio files found under: {input_dir}")

    manifests: dict[str, list[dict]] = {"train": [], "valid": [], "test": []}

    console.print(f"Found {len(audio_files)} audio files. Preparing {clip_seconds}s clips @ {TARGET_SR} Hz.")
    for idx, src in enumerate(tqdm(audio_files, desc="files")):
        track_id = f"track_{idx:07d}"

        # Try to infer metadata from path (e.g. input_dir/Style/Mood/file.wav)
        rel_path = src.relative_to(input_dir)
        path_parts = rel_path.parts[:-1]
        
        style = path_parts[0] if len(path_parts) > 0 else None
        mood = path_parts[1] if len(path_parts) > 1 else None

        try:
            y, sr = load_audio_stereo(src, sr=TARGET_SR)
        except Exception as e:
            console.print(f"[yellow]Skipping unreadable file[/yellow] {src} ({e})")
            continue

        y = lufs_normalize(y, sr=sr, target_lufs=target_lufs)
        clips = slice_clips(y, sr=sr, clip_seconds=clip_seconds, hop_seconds=hop_seconds)
        if not clips:
            continue

        for cidx, clip in enumerate(clips):
            split = _assign_split(rng, spec)
            clip_id = f"{track_id}_c{cidx:04d}"
            out_wav = output_dir / split / track_id / f"{clip_id}.wav"
            write_wav(out_wav, clip, sr=sr)

            desc = build_description(
                genre=default_genre,
                style=style,
                mood=mood,
                bpm=None,
                key=None,
                instrumentation=None,
            )
            cm = ClipMeta(
                audio_path=out_wav,
                track_id=track_id,
                clip_id=clip_id,
                sample_rate=sr,
                duration=float(len(clip)) / float(sr) if sr else 0.0,
                genre=default_genre,
                style=style,
                mood=mood,
                description=desc,
            )
            manifests[split].append(clipmeta_to_audiocraft_row(cm))

    # Guarantee at least 1 example in valid/test when possible
    if not manifests["valid"] and manifests["train"]:
        manifests["valid"].append(manifests["train"].pop())
    if not manifests["test"] and manifests["train"]:
        manifests["test"].append(manifests["train"].pop())

    manifests_dir = output_dir / "manifests"
    out_paths = {}
    for split, rows in manifests.items():
        out_paths[split] = write_jsonl(manifests_dir / f"{split}.jsonl", rows, gzip_compress=gzip_manifest)

    summary = {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "clip_seconds": clip_seconds,
        "hop_seconds": hop_seconds,
        "seed": seed,
        "splits": {k: len(v) for k, v in manifests.items()},
        "manifests": {k: str(v) for k, v in out_paths.items()},
    }
    (output_dir / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    console.print_json(json.dumps(summary))


if __name__ == "__main__":
    app()

