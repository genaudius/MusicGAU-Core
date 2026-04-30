from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass(frozen=True)
class ClipMeta:
    audio_path: Path
    track_id: str
    clip_id: str
    sample_rate: int
    duration: float
    genre: str | None = None
    style: str | None = None
    mood: str | None = None
    technique: str | None = None
    production_context: str | None = None
    bpm: float | None = None
    key: str | None = None
    time_signature: int | None = None
    instrumentation: str | None = None
    description: str | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "path": str(self.audio_path).replace("\\", "/"),
            "track_id": self.track_id,
            "clip_id": self.clip_id,
            "sample_rate": int(self.sample_rate),
            "duration": float(self.duration),
            "genre": self.genre,
            "bpm": self.bpm,
            "key": self.key,
            "time_signature": self.time_signature,
            "mood": self.mood,
            "instrumentation": self.instrumentation,
            "description": self.description,
        }


def build_description(
    *,
    genre: Optional[str],
    style: Optional[str] = None,
    mood: Optional[str] = None,
    technique: Optional[str] = None,
    production_context: Optional[str] = None,
    bpm: Optional[float] = None,
    key: Optional[str] = None,
    instrumentation: Optional[str] = None,
) -> str:
    parts: list[str] = []
    if genre:
        parts.append(genre)
    if style:
        parts.append(style)
    if mood:
        parts.append(mood)
    if technique:
        parts.append(technique)
    if production_context:
        parts.append(production_context)
    if bpm is not None:
        parts.append(f"{round(float(bpm), 1)} BPM")
    if key:
        parts.append(f"tono {key}")
    if instrumentation:
        parts.append(instrumentation)
    
    return ", ".join(parts) if parts else "música"

