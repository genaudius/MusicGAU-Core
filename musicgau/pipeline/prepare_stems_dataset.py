from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from tqdm import tqdm

from musicgau.pipeline.audio import TARGET_SR, load_audio_stereo, peak_normalize, slice_clips, to_mono, write_wav
from musicgau.pipeline.manifest import clipmeta_to_audiocraft_row, write_jsonl
from musicgau.pipeline.schema import ClipMeta, build_description


app = typer.Typer(add_completion=False, help="Prepare STEM clips + JSONL manifests (named stems like bajo/requinto/etc).")
console = Console()


@dataclass(frozen=True)
class SplitSpec:
    train: float = 0.98
    valid: float = 0.01
    test: float = 0.01


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9_\\-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "song"


def _detect_stem_name(path: Path, stem_names: list[str]) -> Optional[str]:
    # Handle cases like "bajo.wav.wav" by stripping common audio suffixes repeatedly.
    name = path.name.lower()
    for _ in range(3):
        for ext in (".wav", ".flac", ".mp3", ".ogg", ".m4a"):
            if name.endswith(ext):
                name = name[: -len(ext)]
                break
    for stem in stem_names:
        stem_l = stem.lower()
        if name == stem_l or name.startswith(stem_l + "_") or name.endswith("_" + stem_l) or stem_l in name:
            return stem
    return None


def _list_audio_files(root: Path) -> list[Path]:
    exts = {".wav", ".flac", ".mp3", ".ogg", ".m4a"}
    files: list[Path] = []
    for p in root.rglob("*"):
        # accept "double extensions" like .wav.wav by checking all suffixes
        suffs = [s.lower() for s in p.suffixes]
        if p.is_file() and any(s in exts for s in suffs):
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
    input_dir: Path = typer.Option(..., exists=True, file_okay=False, help="Root folder with stems organized by song."),
    output_dir: Path = typer.Option(Path("datasets/bachata_stems_v1"), help="Where to write normalized stem clips."),
    genre: str = typer.Option("bachata", help="Genre label to write in metadata."),
    song_id: Optional[str] = typer.Option(
        None,
        help="If stems are stored directly under input_dir (single song), force this song_id (e.g. nadie_muere_por_falta_de_sexo).",
    ),
    artist: Optional[str] = typer.Option(None, help="Optional artist name for local_track_meta when using --song-id."),
    title: Optional[str] = typer.Option(None, help="Optional title for local_track_meta when using --song-id."),
    stem_names: list[str] = typer.Option(
        ["bajo", "requinto", "segunda_guitarra", "bongo", "guira", "kit"],
        help="Stem names to detect from filenames.",
    ),
    include_mixdown: bool = typer.Option(
        True,
        help="Include a non-stem mix/master file as instrumentation=mixdown when detected (recommended).",
    ),
    mixdown_name: str = typer.Option("mixdown", help="Instrumentation label for the master/mixdown track."),
    to_mono_audio: bool = typer.Option(
        False,
        "--to-mono/--keep-stereo",
        help="Downmix stems to mono for training (recommended for MusicGen base).",
    ),
    clip_seconds: float = typer.Option(20.0, help="Clip duration in seconds."),
    hop_seconds: float = typer.Option(10.0, help="Hop duration in seconds (overlap allowed)."),
    seed: int = typer.Option(1234, help="Seed for split assignment."),
    gzip_manifest: bool = typer.Option(True, help="Write manifests as .jsonl.gz"),
    write_local_meta: bool = typer.Option(True, help="Write data/local_track_meta.json mapping song_id -> artist/title."),
) -> None:
    """
    Expected layout (recommended):
      input_dir/
        SongFolder1/
          bajo.wav
          requinto.wav
          segunda_guitarra.wav
          bongo.wav
          guira.wav
          kit.wav
        SongFolder2/
          ...

    Creates:
      output_dir/{split}/{song_id}/{stem}/{song_id}__{stem}__c0000.wav
      output_dir/manifests/{split}.jsonl(.gz)
    """
    rng = random.Random(seed)
    spec = SplitSpec()

    audio_files = _list_audio_files(input_dir)
    if not audio_files:
        raise typer.BadParameter(f"No audio files found under: {input_dir}")

    manifests: dict[str, list[dict]] = {"train": [], "valid": [], "test": []}
    local_meta: dict[str, dict] = {}

    mode = "mono" if to_mono_audio else "stereo"
    console.print(f"Found {len(audio_files)} files. Preparing STEM clips ({mode}) @ {TARGET_SR} Hz.")

    # Pre-detect non-stem candidates per directory for mixdown inclusion.
    by_dir: dict[Path, list[Path]] = {}
    for p in audio_files:
        by_dir.setdefault(p.parent.resolve(), []).append(p)

    for src in tqdm(audio_files, desc="files"):
        stem = _detect_stem_name(src, stem_names)

        # song_id:
        # - If stems are directly under input_dir, user should pass --song-id.
        # - Otherwise, we use parent folder name.
        parent_is_input = src.parent.resolve() == input_dir.resolve()
        song_folder = src.parent.name
        resolved_song_id = _slug(song_id) if (parent_is_input and song_id) else _slug(song_folder)
        if parent_is_input and not song_id:
            # Avoid producing "bachata" or drive-root-like ids; require explicit song_id in this layout.
            console.print(
                f"[yellow]Skipping[/yellow] {src} because stems are in the root folder; "
                f"re-run with --song-id to name the track."
            )
            continue

        # Decide instrumentation:
        # - If it's a known stem -> use that stem
        # - Else, optionally treat a single non-stem file in the directory as mixdown
        instrumentation: Optional[str] = stem
        if instrumentation is None and include_mixdown:
            # "single-song folder" case: if there is exactly one non-stem audio file in this dir, use it as mixdown.
            candidates = []
            for p in by_dir.get(src.parent.resolve(), []):
                if _detect_stem_name(p, stem_names) is None:
                    candidates.append(p)
            if len(candidates) == 1 and src.resolve() == candidates[0].resolve():
                instrumentation = mixdown_name

        if instrumentation is None:
            continue

        # naive metadata guess: "Artist - Title" folder convention
        if resolved_song_id not in local_meta:
            a_guess = "unknown"
            t_guess = song_folder
            if parent_is_input and song_id:
                a_guess = artist or "unknown"
                t_guess = title or resolved_song_id
            elif " - " in song_folder:
                a, t = song_folder.split(" - ", 1)
                a_guess = a.strip() or "unknown"
                t_guess = t.strip() or song_folder
            local_meta[resolved_song_id] = {"artist": a_guess, "title": t_guess, "isrc": None}

        try:
            y, sr = load_audio_stereo(src, sr=TARGET_SR)
        except Exception as e:
            console.print(f"[yellow]Skipping unreadable file[/yellow] {src} ({e})")
            continue

        if to_mono_audio:
            y = to_mono(y)

        y = peak_normalize(y)
        clips = slice_clips(y, sr=sr, clip_seconds=clip_seconds, hop_seconds=hop_seconds)
        if not clips:
            continue

        for cidx, clip in enumerate(clips):
            split = _assign_split(rng, spec)
            clip_id = f"{resolved_song_id}__{instrumentation}__c{cidx:04d}"
            out_wav = output_dir / split / resolved_song_id / instrumentation / f"{clip_id}.wav"
            write_wav(out_wav, clip, sr=sr)

            desc = build_description(
                genre=genre,
                bpm=None,
                key=None,
                mood=None,
                instrumentation=instrumentation,
            )
            cm = ClipMeta(
                audio_path=out_wav,
                track_id=resolved_song_id,
                clip_id=clip_id,
                sample_rate=sr,
                duration=float(len(clip)) / float(sr) if sr else 0.0,
                genre=genre,
                instrumentation=instrumentation,
                description=desc,
            )
            manifests[split].append(clipmeta_to_audiocraft_row(cm))

    if not manifests["valid"] and manifests["train"]:
        manifests["valid"].append(manifests["train"].pop())
    if not manifests["test"] and manifests["train"]:
        manifests["test"].append(manifests["train"].pop())

    manifests_dir = output_dir / "manifests"
    out_paths = {}
    for split, rows in manifests.items():
        out_paths[split] = write_jsonl(manifests_dir / f"{split}.jsonl", rows, gzip_compress=gzip_manifest)

    if write_local_meta:
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "local_track_meta.json").write_text(json.dumps(local_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "genre": genre,
        "stem_names": stem_names,
        "clip_seconds": clip_seconds,
        "hop_seconds": hop_seconds,
        "seed": seed,
        "splits": {k: len(v) for k, v in manifests.items()},
        "manifests": {k: str(v) for k, v in out_paths.items()},
        "songs_detected": len(local_meta),
    }
    (output_dir / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    console.print_json(json.dumps(summary))


if __name__ == "__main__":
    app()

