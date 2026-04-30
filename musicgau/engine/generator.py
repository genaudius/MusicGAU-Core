from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import soundfile as sf

from musicgau import MODEL_NAME
from musicgau.engine.presets import get_preset


@dataclass(frozen=True)
class GenerateRequest:
    prompt: str
    genre: str = "salsa"
    bpm: Optional[float] = None
    key: Optional[str] = None
    seconds: int = 30
    seed: int = 42
    base_model: str = "facebook/musicgen-small"


def _build_conditioned_prompt(req: GenerateRequest) -> str:
    preset = get_preset(req.genre)
    bpm = req.bpm if req.bpm is not None else (preset.default_bpm if preset else None)
    parts: list[str] = []
    if preset:
        parts.append(preset.prompt_prefix)
        parts.append(f"instruments: {preset.instruments_hint}")
        parts.append(f"time_signature: {preset.time_signature}")
    if bpm is not None:
        parts.append(f"bpm: {round(float(bpm), 2)}")
    if req.key:
        parts.append(f"key: {req.key}")
    parts.append(req.prompt)
    return ", ".join([p for p in parts if p])


def generate_to_wav(req: GenerateRequest, out_wav: Path) -> dict:
    """
    Generate audio using AudioCraft MusicGen (pretrained or later fine-tuned).

    We import heavy deps lazily so the rest of the repo works without GPU installs.
    """
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    prompt = _build_conditioned_prompt(req)

    try:
        import torch  # noqa: F401
        from audiocraft.models import MusicGen
    except Exception as e:
        meta = {
            "model_name": MODEL_NAME,
            "status": "error_missing_deps",
            "error": str(e),
            "note": "Install requirements and ensure CUDA torch wheels if using GPU.",
        }
        (out_wav.with_suffix(".json")).write_text(__import__("json").dumps(meta, indent=2), encoding="utf-8")
        raise

    model = MusicGen.get_pretrained(req.base_model)
    model.set_generation_params(duration=float(req.seconds), top_k=250, top_p=0.0, temperature=1.0)

    import torch

    torch.manual_seed(int(req.seed))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(req.seed))

    wav = model.generate([prompt], progress=True)  # [B, C, T]
    wav_np = wav[0].detach().cpu().float().numpy().T  # [T, C]

    sr = getattr(model, "sample_rate", 32000)
    sf.write(str(out_wav), wav_np, sr, subtype="PCM_16")

    meta = {
        "model_name": MODEL_NAME,
        "status": "ok",
        "base_model": req.base_model,
        "prompt": req.prompt,
        "conditioned_prompt": prompt,
        "genre": req.genre,
        "bpm": req.bpm,
        "key": req.key,
        "seconds": req.seconds,
        "seed": req.seed,
        "sample_rate": sr,
        "output_wav": str(out_wav),
    }
    (out_wav.with_suffix(".json")).write_text(
        __import__("json").dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta

