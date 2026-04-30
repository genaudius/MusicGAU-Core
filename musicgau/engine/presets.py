from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GenrePreset:
    key: str
    label: str
    bpm_min: float
    bpm_max: float
    default_bpm: float
    time_signature: str
    instruments_hint: str
    prompt_prefix: str


PRESETS: dict[str, GenrePreset] = {
    "salsa": GenrePreset(
        key="salsa",
        label="Salsa",
        bpm_min=150,
        bpm_max=210,
        default_bpm=180,
        time_signature="4/4",
        instruments_hint="congas, bongos, timbales, clave, piano montuno, brass section, bass",
        prompt_prefix="latin salsa, energetic, danceable",
    ),
    "merengue": GenrePreset(
        key="merengue",
        label="Merengue",
        bpm_min=150,
        bpm_max=210,
        default_bpm=185,
        time_signature="4/4",
        instruments_hint="tambora, guira, accordion or sax, bass, piano",
        prompt_prefix="dominican merengue, fast, festive, bright",
    ),
    "bachata": GenrePreset(
        key="bachata",
        label="Bachata",
        bpm_min=110,
        bpm_max=160,
        default_bpm=132,
        time_signature="4/4",
        instruments_hint="requinto guitar, rhythm guitar, bongos, guira, bass",
        prompt_prefix="dominican bachata, romantic, guitar-driven",
    ),
    "cumbia": GenrePreset(
        key="cumbia",
        label="Cumbia",
        bpm_min=80,
        bpm_max=120,
        default_bpm=96,
        time_signature="4/4",
        instruments_hint="tambora, guacharaca, bass, accordion, synth pads",
        prompt_prefix="cumbia, tropical, groovy, steady percussion",
    ),
}


def get_preset(genre: str) -> Optional[GenrePreset]:
    if not genre:
        return None
    g = genre.strip().lower()
    return PRESETS.get(g)

