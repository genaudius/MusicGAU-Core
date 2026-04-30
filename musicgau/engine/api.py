from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from musicgau.engine.generator import GenerateRequest, generate_to_wav


app = FastAPI(title="MusicGAU Engine", version="0.1.0")


class GenerateBody(BaseModel):
    prompt: str = Field(..., min_length=1)
    genre: str = "salsa"
    bpm: Optional[float] = None
    key: Optional[str] = None
    seconds: int = 30
    seed: int = 42
    base_model: str = "facebook/musicgen-small"
    out_wav: str = "outputs/api_out.wav"


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/generate")
def generate(body: GenerateBody) -> dict:
    req = GenerateRequest(
        prompt=body.prompt,
        genre=body.genre,
        bpm=body.bpm,
        key=body.key,
        seconds=body.seconds,
        seed=body.seed,
        base_model=body.base_model,
    )
    meta = generate_to_wav(req, Path(body.out_wav))
    return meta

