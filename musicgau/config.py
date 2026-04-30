from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def _load_dotenv() -> None:
    """
    Load environment variables from .env if present.

    We try:
    - GenAudius_V1/.env (recommended)
    - GenAudius_V1/../.env (in case user keeps a shared .env at project parent)
    """
    try:
        from dotenv import load_dotenv
    except Exception:
        return

    root = Path(__file__).resolve().parents[1]
    candidates = [
        root / ".env",
        root.parent / ".env",
    ]
    for p in candidates:
        if p.exists():
            load_dotenv(dotenv_path=p, override=False)


_load_dotenv()


def _env(key: str, default: str | None = None) -> str | None:
    v = os.getenv(key)
    return v if v is not None and v != "" else default


def _env_any(keys: list[str]) -> str | None:
    for k in keys:
        v = _env(k)
        if v is not None:
            return v
    return None


@dataclass(frozen=True)
class AppPaths:
    repo_root: Path
    data_dir: Path
    cache_dir: Path
    outputs_dir: Path
    checkpoints_dir: Path


def get_paths(repo_root: Path | None = None) -> AppPaths:
    root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    data_dir = root / "data"
    cache_dir = root / "cache"
    outputs_dir = root / "outputs"
    checkpoints_dir = root / "checkpoints"
    return AppPaths(
        repo_root=root,
        data_dir=data_dir,
        cache_dir=cache_dir,
        outputs_dir=outputs_dir,
        checkpoints_dir=checkpoints_dir,
    )


@dataclass(frozen=True)
class ApiKeys:
    spotify_client_id: str | None
    spotify_client_secret: str | None
    lastfm_api_key: str | None


def get_api_keys() -> ApiKeys:
    return ApiKeys(
        # Accept both conventions: SPOTIFY_* (this repo) and SPOTIPY_* (common in Spotipy setups).
        spotify_client_id=_env_any(["SPOTIFY_CLIENT_ID", "SPOTIPY_CLIENT_ID"]),
        spotify_client_secret=_env_any(["SPOTIFY_CLIENT_SECRET", "SPOTIPY_CLIENT_SECRET"]),
        lastfm_api_key=_env("LASTFM_API_KEY"),
    )

