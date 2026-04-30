from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from tqdm import tqdm

from musicgau.config import get_api_keys, get_paths
from musicgau.integrations.cache_db import CacheDB
from musicgau.integrations.lastfm import LastfmClient
from musicgau.integrations.spotify import SpotifyClient
from musicgau.pipeline.schema import build_description


app = typer.Typer(add_completion=False, help="Enrich JSONL manifests with Spotify + Last.fm metadata.")
console = Console()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if str(path).endswith(".gz"):
        with gzip.open(str(path), "rt", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if str(path).endswith(".gz"):
        with gzip.open(str(path), "wt", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    else:
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


@dataclass(frozen=True)
class LocalTrackMeta:
    artist: str
    title: str
    isrc: Optional[str] = None


@app.command()
def run(
    manifest_in: Path = typer.Option(..., exists=True, help="Input manifest .jsonl or .jsonl.gz"),
    manifest_out: Path = typer.Option(..., help="Output enriched manifest"),
    local_meta_json: Optional[Path] = typer.Option(
        None,
        help="Optional JSON mapping track_id -> {artist,title,isrc}. If missing, only default_genre/prompt is used.",
    ),
    default_genre: Optional[str] = typer.Option(None, help="Fallback genre if unavailable."),
    market: str = typer.Option("US", help="Spotify market for search."),
) -> None:
    paths = get_paths()
    keys = get_api_keys()
    cache = CacheDB(paths.cache_dir / "api_cache.sqlite3")
    cache.init()

    spotify: SpotifyClient | None = None
    if keys.spotify_client_id and keys.spotify_client_secret:
        spotify = SpotifyClient(keys.spotify_client_id, keys.spotify_client_secret, cache)
    lastfm: LastfmClient | None = None
    if keys.lastfm_api_key:
        lastfm = LastfmClient(keys.lastfm_api_key, cache)

    local_map: dict[str, LocalTrackMeta] = {}
    if local_meta_json is not None and local_meta_json.exists():
        raw = json.loads(local_meta_json.read_text(encoding="utf-8"))
        for k, v in raw.items():
            if isinstance(v, dict) and v.get("artist") and v.get("title"):
                local_map[str(k)] = LocalTrackMeta(artist=str(v["artist"]), title=str(v["title"]), isrc=v.get("isrc"))

    rows = _read_jsonl(manifest_in)
    console.print(f"Loaded {len(rows)} rows from {manifest_in}")

    for r in tqdm(rows, desc="enrich"):
        track_id = str(r.get("track_id", ""))
        lm = local_map.get(track_id)

        genre = r.get("genre") or default_genre
        bpm = r.get("bpm")
        key = r.get("key")
        mood = r.get("mood")
        instrumentation = r.get("instrumentation")

        if spotify is not None and lm is not None:
            try:
                s = spotify.search_track(artist=lm.artist, title=lm.title, isrc=lm.isrc, market=market)
                items = (((s.get("tracks") or {}).get("items")) or [])
                if items:
                    best = items[0]
                    sid = best.get("id")
                    if sid:
                        r.setdefault("spotify", {})
                        r["spotify"]["track_id"] = sid
                        af = spotify.get_audio_features(str(sid))
                        r["spotify"]["audio_features"] = af
                        bpm = bpm or af.get("tempo")
                        r["spotify"]["key"] = af.get("key")
                        r["spotify"]["mode"] = af.get("mode")
                        r["spotify"]["time_signature"] = af.get("time_signature")
            except Exception:
                pass

        if lastfm is not None and lm is not None:
            try:
                p = lastfm.track_get_top_tags(artist=lm.artist, track=lm.title)
                tags = lastfm.extract_top_tags(p, limit=10)
                if tags:
                    r.setdefault("lastfm", {})
                    r["lastfm"]["top_tags"] = tags
                    if mood is None:
                        mood = tags[0]
            except Exception:
                pass

        desc = r.get("description") or build_description(
            genre=str(genre) if genre else None,
            bpm=float(bpm) if bpm is not None else None,
            key=str(key) if key else None,
            mood=str(mood) if mood else None,
            instrumentation=str(instrumentation) if instrumentation else None,
        )
        r["description"] = desc
        r["text"] = desc

        if genre and not r.get("genre"):
            r["genre"] = genre
        if bpm is not None and r.get("bpm") is None:
            r["bpm"] = bpm

    _write_jsonl(manifest_out, rows)
    console.print(f"Wrote enriched manifest to {manifest_out}")


if __name__ == "__main__":
    app()

