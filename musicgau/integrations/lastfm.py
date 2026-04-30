from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import urllib.parse

import requests

from musicgau.integrations.cache_db import CacheDB


LASTFM_API_BASE = "https://ws.audioscrobbler.com/2.0/"


@dataclass
class LastfmClient:
    api_key: str
    cache: CacheDB

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        p = dict(params)
        p["api_key"] = self.api_key
        p["format"] = "json"
        r = requests.get(LASTFM_API_BASE, params=p, timeout=30)
        r.raise_for_status()
        return r.json()

    def track_get_top_tags(self, *, artist: str, track: str, autocorrect: int = 1) -> dict[str, Any]:
        key = urllib.parse.quote_plus(f"track_getTopTags|{artist}|{track}|{autocorrect}")
        cached = self.cache.get("lastfm", key)
        if cached is not None:
            return cached
        data = self._get(
            {
                "method": "track.getTopTags",
                "artist": artist,
                "track": track,
                "autocorrect": autocorrect,
            }
        )
        self.cache.set("lastfm", key, data)
        return data

    @staticmethod
    def extract_top_tags(payload: dict[str, Any], limit: int = 10) -> list[str]:
        tags_obj = payload.get("toptags", {}) if isinstance(payload, dict) else {}
        tags = tags_obj.get("tag", [])
        if tags is None:
            return []
        if isinstance(tags, dict):
            tags = [tags]
        out: list[str] = []
        for t in tags:
            name = t.get("name") if isinstance(t, dict) else None
            if name:
                out.append(str(name))
            if len(out) >= limit:
                break
        return out

