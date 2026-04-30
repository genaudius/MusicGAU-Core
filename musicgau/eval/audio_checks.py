from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf


@dataclass(frozen=True)
class AudioCheckResult:
    path: str
    sample_rate: int
    seconds: float
    peak: float
    rms: float
    clipped_samples: int
    silence_ratio: float


def run_basic_checks(path: Path, silence_thresh: float = 1e-4) -> AudioCheckResult:
    y, sr = sf.read(str(path), always_2d=True)
    y = y.astype(np.float32, copy=False)

    peak = float(np.max(np.abs(y))) if y.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(y)))) if y.size else 0.0
    clipped = int(np.sum(np.abs(y) >= 0.999))
    silence_ratio = float(np.mean(np.abs(y) < silence_thresh)) if y.size else 1.0
    seconds = float(y.shape[0]) / float(sr) if sr else 0.0

    return AudioCheckResult(
        path=str(path),
        sample_rate=int(sr),
        seconds=seconds,
        peak=peak,
        rms=rms,
        clipped_samples=clipped,
        silence_ratio=silence_ratio,
    )

