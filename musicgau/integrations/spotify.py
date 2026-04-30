from __future__ import annotations

import base64
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Optional

import requests

from musicgau.integrations.cache_db import CacheDB


SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"


@dataclass
class SpotifyClient:
    client_id: str
    client_secret: str
    cache: CacheDB

    _token: Optional[str] = None
    _token_exp: float = 0.0

    def _get_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_exp - 30:
            return self._token

        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("ascii")
        r = requests.post(
            SPOTIFY_TOKEN_URL,
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        self._token = data["access_token"]
        self._token_exp = now + float(data.get("expires_in", 3600))
        return self._token

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        token = self._get_token()
        url = f"{SPOTIFY_API_BASE}{path}"
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def search_track(
        self,
        *,
        artist: str,
        title: str,
        isrc: str | None = None,
        market: str = "US",
        limit: int = 5,
    ) -> dict[str, Any]:
        q_parts = [f'track:\"{title}\"', f'artist:\"{artist}\"']
        if isrc:
            q_parts.append(f"isrc:{isrc}")
        q = " ".join(q_parts)
        key = urllib.parse.quote_plus(f"search_track|{market}|{limit}|{q}")
        cached = self.cache.get("spotify", key)
        if cached is not None:
            return cached

        data = self._get("/search", params={"q": q, "type": "track", "limit": limit, "market": market})
        self.cache.set("spotify", key, data)
        return data

    def get_audio_features(self, track_id: str) -> dict[str, Any]:
        key = f"audio_features|{track_id}"
        cached = self.cache.get("spotify", key)
        if cached is not None:
            return cached
        data = self._get(f"/audio-features/{track_id}")
        self.cache.set("spotify", key, data)
        return data

