import os
import random
from typing import Dict, Any, List, Optional
from musicgau.integrations.spotify import SpotifyClient
from musicgau.integrations.lastfm import LastfmClient
from musicgau.integrations.cache_db import CacheDB
from musicgau.config import get_api_keys, get_paths

class MusicGAUTrendService:
    def __init__(self):
        self.keys = get_api_keys()
        self.paths = get_paths()
        self.cache = CacheDB(self.paths.cache_dir / "trends_cache.sqlite3")
        self.cache.init()
        
        self.spotify = SpotifyClient(
            client_id=self.keys.spotify_client_id,
            client_secret=self.keys.spotify_client_secret,
            cache=self.cache
        )
        self.lastfm = LastfmClient(
            api_key=self.keys.lastfm_api_key,
            cache=self.cache
        )

    def get_tropical_trends(self, country: str = "Dominican Republic") -> Dict[str, Any]:
        """
        Fetches trending tropical music metadata from Last.fm and Spotify.
        """
        print(f"[Trends] Fetching trends for {country}...")
        
        # 1. Get Top Tracks from Last.fm for the region
        try:
            # Last.fm geo.getTopTracks
            geo_data = self.lastfm._get({
                "method": "geo.getTopTracks",
                "country": country,
                "limit": 10
            })
            tracks = geo_data.get("tracks", {}).get("track", [])
        except Exception as e:
            print(f"[Trends] Last.fm Error: {e}")
            tracks = []

        # 2. Extract features from a sample of trending tracks via Spotify
        total_energy = 0.0
        total_bpm = 0.0
        count = 0
        
        trending_genres = ["bachata", "merengue"] # Default focus
        
        for t in tracks[:5]:
            artist = t.get("artist", {}).get("name")
            title = t.get("name")
            
            try:
                s_search = self.spotify.search_track(artist=artist, title=title, limit=1)
                items = s_search.get("tracks", {}).get("items", [])
                if items:
                    tid = items[0]["id"]
                    features = self.spotify.get_audio_features(tid)
                    if features:
                        total_energy += features.get("energy", 0.5)
                        total_bpm += features.get("tempo", 120)
                        count += 1
            except Exception:
                continue

        avg_energy = total_energy / count if count > 0 else 0.7
        avg_bpm = total_bpm / count if count > 0 else 130
        
        return {
            "avg_energy": avg_energy,
            "avg_bpm": avg_bpm,
            "trending_tracks": [f"{t.get('artist', {}).get('name')} - {t.get('name')}" for t in tracks[:5]],
            "market": country
        }

    def get_prompt_injection(self, genre: str = "bachata") -> str:
        """
        Generates a string to inject into the prompt based on current trends.
        """
        trends = self.get_tropical_trends()
        energy = trends["avg_energy"]
        bpm = trends["avg_bpm"]
        
        intensity = "highly energetic" if energy > 0.75 else "smooth"
        
        return f"Currently trending in {trends['market']}: {intensity} {genre} style, approximately {bpm:.0f} BPM."

if __name__ == "__main__":
    # Test
    service = MusicGAUTrendService()
    print(service.get_prompt_injection("bachata"))
