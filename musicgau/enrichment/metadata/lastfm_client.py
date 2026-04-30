import os
import pylast
from dotenv import load_dotenv
from pathlib import Path

class MusicGAULastFMClient:
    def __init__(self):
        # Look for .env in current, GenAudius_V1, and MusicGAU roots
        root = Path(__file__).resolve().parents[3]
        dotenv_path = root / ".env"
        if not dotenv_path.exists():
            dotenv_path = root.parent / ".env"
            
        load_dotenv(dotenv_path)
        api_key = os.getenv("LASTFM_API_KEY")
        
        # Last.fm doesn't strictly need a secret for public data, but we follow standard practice
        self.network = pylast.LastFMNetwork(api_key=api_key)

    def get_track_tags(self, artist: str, track_name: str, limit: int = 5):
        """
        Returns top community tags for a track.
        """
        try:
            track = self.network.get_track(artist, track_name)
            top_tags = track.get_top_tags(limit=limit)
            return [tag.item.get_name() for tag in top_tags]
        except Exception as e:
            print(f"Last.fm error: {e}")
            return []

    def get_artist_tags(self, artist: str, limit: int = 5):
        """
        Returns top tags for an artist (useful for genre fallback).
        """
        try:
            artist_obj = self.network.get_artist(artist)
            top_tags = artist_obj.get_top_tags(limit=limit)
            return [tag.item.get_name() for tag in top_tags]
        except Exception as e:
            print(f"Last.fm error: {e}")
            return []

    def get_contextual_tags(self, artist: str, track_name: str):
        """
        Combines track and artist tags for a deep contextual profile.
        """
        track_tags = self.get_track_tags(artist, track_name)
        artist_tags = self.get_artist_tags(artist)
        
        # Deduplicate and merge
        all_tags = list(dict.fromkeys(track_tags + artist_tags))
        return all_tags

if __name__ == "__main__":
    client = MusicGAULastFMClient()
    tags = client.get_contextual_tags("Aventura", "Obsesion")
    print(f"Tags found: {tags}")
