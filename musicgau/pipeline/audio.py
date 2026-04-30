from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf
import librosa


TARGET_SR = 32000


def load_audio_stereo(path: Path, sr: int = TARGET_SR) -> Tuple[np.ndarray, int]:
    """
    Load audio and keep it stereo when available.

    Returns:
      - y: shape [T, C] where C is 1 or 2 (or more channels if present)
    """
    y, native_sr = sf.read(str(path), always_2d=True)
    y = y.astype(np.float32, copy=False)
    if native_sr != sr:
        # librosa expects [T] or [C, T]; we transpose to [C, T] then back.
        y_ct = y.T
        y_ct = librosa.resample(y_ct, orig_sr=native_sr, target_sr=sr, axis=-1)
        y = y_ct.T
    return y, sr


def to_mono(y: np.ndarray) -> np.ndarray:
    """
    Downmix multi-channel audio [T, C] -> mono [T, 1] by averaging channels.
    """
    if y.ndim == 1:
        return y.astype(np.float32, copy=False)[:, None]
    if y.ndim != 2:
        raise ValueError(f"Expected audio with shape [T, C], got {y.shape}")
    if y.shape[1] == 1:
        return y
    return np.mean(y, axis=1, keepdims=True).astype(np.float32, copy=False)


def peak_normalize(y: np.ndarray, peak: float = 0.98) -> np.ndarray:
    m = float(np.max(np.abs(y))) if y.size else 0.0
    if m <= 0:
        return y
    g = peak / m
    return (y * g).astype(np.float32, copy=False)


def lufs_normalize(y: np.ndarray, sr: int, target_lufs: float = -14.0) -> np.ndarray:
    """
    Normalize audio to target LUFS using pyloudnorm.
    y expected shape: [T, C]
    """
    try:
        import pyloudnorm as pyln
        # pyloudnorm expects [T, C]
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(y)
        # Handle -inf or very low loudness
        if loudness < -70:
            return y
        y_norm = pyln.normalize.loudness(y, loudness, target_lufs)
        # Peak limit to avoid clipping after LUFS normalization
        m = np.max(np.abs(y_norm))
        if m > 0.99:
            y_norm = y_norm * (0.99 / m)
        return y_norm.astype(np.float32, copy=False)
    except ImportError:
        # Fallback to peak normalize if pyloudnorm is missing
        return peak_normalize(y)


def write_wav(path: Path, y: np.ndarray, sr: int = TARGET_SR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), y, sr, subtype="PCM_16")


def slice_clips(
    y: np.ndarray,
    sr: int,
    clip_seconds: float,
    hop_seconds: float,
) -> list[np.ndarray]:
    clip_len = int(round(clip_seconds * sr))
    hop_len = int(round(hop_seconds * sr))
    if clip_len <= 0 or hop_len <= 0:
        raise ValueError("clip_seconds and hop_seconds must be > 0")
    # y is [T, C]
    if y.shape[0] < clip_len:
        return []
    clips: list[np.ndarray] = []
    for start in range(0, y.shape[0] - clip_len + 1, hop_len):
        clips.append(y[start : start + clip_len, :])
    return clips

