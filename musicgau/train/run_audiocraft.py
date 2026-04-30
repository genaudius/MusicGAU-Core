from __future__ import annotations

import json
import subprocess
from pathlib import Path
import os
import sys

import typer
from rich.console import Console


app = typer.Typer(add_completion=False, help="Run AudioCraft training/eval/export with reproducible commands.")
console = Console()


def _ensure_exists(p: Path, label: str) -> None:
    if not p.exists():
        raise typer.BadParameter(f"Missing {label}: {p}")


# Bundled AudioCraft dset configs (under audiocraft_repo/config/dset/) with full datasource.*
# so Dora can build an XP (see dora.hydra._get_delta vs ++datasource-only overrides).
_MANIFEST_TRIO_TO_DSET: dict[tuple[str, str, str], str] = {
    (
        "datasets/bachata_stems_v1/manifests/train.enriched.jsonl.gz",
        "datasets/bachata_stems_v1/manifests/valid.jsonl.gz",
        "datasets/bachata_stems_v1/manifests/test.jsonl.gz",
    ): "audio/musicgau_bachata_32khz",
    (
        "datasets/bachata_stems_mono_v1/manifests/train.enriched.jsonl.gz",
        "datasets/bachata_stems_mono_v1/manifests/valid.jsonl.gz",
        "datasets/bachata_stems_mono_v1/manifests/test.jsonl.gz",
    ): "audio/musicgau_bachata_mono_32khz",
}


def _manifest_paths_relative_to_cwd(cwd: Path, *paths: Path) -> tuple[str, ...]:
    cwd = cwd.resolve()
    return tuple(p.resolve().relative_to(cwd).as_posix() for p in paths)


def _resolve_hydra_dset(hydra_dset: str, cwd: Path, train_m: Path, valid_m: Path, eval_m: Path) -> str:
    if hydra_dset not in {"", "auto"}:
        return hydra_dset
    trio = _manifest_paths_relative_to_cwd(cwd, train_m, valid_m, eval_m)
    preset = _MANIFEST_TRIO_TO_DSET.get(trio)
    if preset:
        return preset
    raise typer.BadParameter(
        "Could not map manifests to a bundled Hydra dset preset (needed for Dora XP). "
        f"Got train/valid/eval relative paths:\n  {trio[0]}\n  {trio[1]}\n  {trio[2]}\n"
        "Add a YAML under audiocraft_repo/config/dset/audio/ (copy musicgau_bachata_32khz.yaml) "
        "and pass --hydra-dset audio/your_file (without .yaml). "
        "Or use train.enriched + valid + test under datasets/bachata_stems_v1 or bachata_stems_mono_v1."
    )


@app.command()
def train(
    dataset_root: Path = typer.Option(Path("datasets/musicgau_clips"), help="Dataset root produced by prepare_dataset."),
    out_dir: Path = typer.Option(Path("checkpoints/musicgau"), help="Output checkpoint directory."),
    solver_config: str = typer.Option(
        "musicgen/musicgen_base_32khz",
        help="AudioCraft solver config group (e.g. musicgen/musicgen_base_32khz).",
    ),
    channels: int = typer.Option(1, help="Target channels for training config (MusicGen base is mono=1)."),
    max_steps: int = typer.Option(5000, help="Max training steps."),
    batch_size: int = typer.Option(4, help="Batch size per GPU."),
    lr: float = typer.Option(1e-4, help="Learning rate."),
    dry_run: bool = typer.Option(True, help="Print command only (recommended first)."),
    train_manifest: Path | None = typer.Option(
        None,
        help="Optional explicit train manifest path. If omitted, will prefer train.enriched.jsonl(.gz) when present.",
    ),
    valid_manifest: Path | None = typer.Option(
        None,
        help="Optional explicit valid manifest path. If omitted, uses manifests/valid.jsonl(.gz).",
    ),
    eval_manifest: Path | None = typer.Option(
        None,
        help="Optional explicit eval manifest path. If omitted, will use manifests/test.jsonl(.gz) when present, else reuse valid.",
    ),
    use_multirun: bool = typer.Option(
        False,
        help="Hydra --multirun (disables Dora XP; breaks AudioCraft train with 'Not in a xp!'). Leave off.",
    ),
    hydra_dset: str = typer.Option(
        "auto",
        help="Hydra dset=... config group. 'auto' picks a bundled preset from manifest paths (Dora-safe).",
    ),
    device: str = typer.Option(
        "auto",
        help="Training device override (auto/cpu/cuda); auto uses CUDA when available.",
    ),
) -> None:
    if train_manifest is not None:
        train_m = train_manifest
    else:
        # Prefer enriched manifest if available
        train_m = dataset_root / "manifests" / "train.enriched.jsonl.gz"
        if not train_m.exists():
            train_m = dataset_root / "manifests" / "train.enriched.jsonl"
        if not train_m.exists():
            train_m = dataset_root / "manifests" / "train.jsonl.gz"
        if not train_m.exists():
            train_m = dataset_root / "manifests" / "train.jsonl"

    if valid_manifest is not None:
        valid_m = valid_manifest
    else:
        valid_m = dataset_root / "manifests" / "valid.jsonl.gz"
        if not valid_m.exists():
            valid_m = dataset_root / "manifests" / "valid.jsonl"

    if eval_manifest is not None:
        eval_m = eval_manifest
    else:
        eval_m = dataset_root / "manifests" / "test.jsonl.gz"
        if not eval_m.exists():
            eval_m = dataset_root / "manifests" / "test.jsonl"
        if not eval_m.exists():
            eval_m = valid_m

    _ensure_exists(train_m, "train manifest")
    _ensure_exists(valid_m, "valid manifest")
    _ensure_exists(eval_m, "eval manifest")

    out_dir.mkdir(parents=True, exist_ok=True)

    if device not in {"auto", "cpu", "cuda"}:
        raise typer.BadParameter("device must be one of: auto, cpu, cuda")

    # Auto-select device: many Windows setups have CPU-only torch.
    resolved_device = device
    if device == "auto":
        try:
            import torch  # type: ignore

            resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            resolved_device = "cpu"

    cwd = Path.cwd()
    dset_group = _resolve_hydra_dset(hydra_dset, cwd, train_m, valid_m, eval_m)

    # Dora's HydraMain skips XP setup when argv contains --multirun, which breaks
    # flashy.setup_logging ("Not in a xp!"). Prefer plain Hydra unless you know you need multirun.
    cmd = [
        sys.executable,
        "-m",
        "audiocraft.train",
        "--multirun" if use_multirun else "",
        f"solver={solver_config}",
        f"dset={dset_group}",
        f"optim.lr={lr}",
        f"++dataset.batch_size={batch_size}",
        f"++schedule.total_updates={max_steps}",
        f"++channels={channels}",
        f"++logging.dir={out_dir.as_posix()}",
        f"++device={resolved_device}",
    ]
    # Windows doesn't support 'forkserver' start method used in some AudioCraft configs.
    if sys.platform.startswith("win"):
        # mp_start_method exists in config; use ++ to override.
        cmd.append("++mp_start_method=spawn")
        # DataLoader workers + spawn re-import audiocraft.train and hit dora HydraMain
        # IndexError in worker processes; 0 workers avoids that.
        cmd.append("++dataset.num_workers=0")
        cmd.append("++evaluate.num_workers=0")
        cmd.append("++generate.num_workers=0")
    cmd = [c for c in cmd if c != ""]

    console.print("[bold]AudioCraft train command (generated)[/bold]")
    console.print(" ".join(cmd))

    if dry_run:
        console.print("\nSet --dry-run false to execute (after verifying your AudioCraft version supports this entrypoint).")
        return

    # AudioCraft/Dora configs sometimes reference ${oc.env:USER}, which isn't set on Windows by default.
    env = dict(os.environ)
    if "USER" not in env or not env["USER"]:
        env["USER"] = env.get("USERNAME", "user")

    subprocess.run(cmd, check=True, env=env)


@app.command()
def export(
    checkpoint_dir: Path = typer.Option(Path("checkpoints/musicgau"), help="Training outputs directory."),
    export_dir: Path = typer.Option(Path("checkpoints/musicgau_export"), help="Export directory for inference."),
) -> None:
    checkpoint_dir = checkpoint_dir.resolve()
    export_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "checkpoint_dir": str(checkpoint_dir),
        "export_dir": str(export_dir.resolve()),
        "status": "not_implemented",
        "note": "Wire this to your AudioCraft checkpoint format (Dora sig or raw .pt).",
    }
    (export_dir / "export_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    console.print(f"Wrote {export_dir / 'export_meta.json'}")


if __name__ == "__main__":
    app()

