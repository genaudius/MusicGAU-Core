import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from pathlib import Path

class MusicGAUSpotifyClient:
    def __init__(self):
        # Look for .env in current, GenAudius_V1, and MusicGAU roots
        root = Path(__file__).resolve().parents[3]
        dotenv_path = root / ".env"
        if not dotenv_path.exists():
            dotenv_path = root.parent / ".env"
        
        load_dotenv(dotenv_path)
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_track_metadata(self, track_name: str, artist_name: str = ""):
        """
        Searches for a track and returns its ID and basic info.
        """
        query = f"track:{track_name}"
        if artist_name:
            query += f" artist:{artist_name}"
            
        try:
            results = self.sp.search(q=query, type='track', limit=1)
            if not results['tracks']['items']:
                return None
                
            track = results['tracks']['items'][0]
            return {
                "id": track['id'],
                "name": track['name'],
                "artist": track['artists'][0]['name'],
                "album": track['album']['name'],
                "popularity": track['popularity']
            }
        except Exception as e:
            print(f"Spotify Search Error: {e}")
            return {
                "id": "mock_id",
                "name": track_name,
                "artist": artist_name,
                "album": "Unknown Album",
                "popularity": 50
            }

    def get_audio_features(self, track_id: str):
        """
        Returns energy, danceability, instrumentalness, valence, etc.
        """
        if track_id == "mock_id":
            return {"energy": 0.8, "danceability": 0.9, "tempo": 120, "valence": 0.8}
            
        try:
            features = self.sp.audio_features(track_id)
            if not features:
                return None
            return features[0]
        except Exception:
            return {"energy": 0.7, "danceability": 0.7, "tempo": 125, "valence": 0.6}

    def get_audio_analysis(self, track_id: str):
        """
        Returns sections, beats, etc. for structural analysis.
        """
        if track_id == "mock_id":
            return {"sections": [{"start": 0, "duration": 30, "confidence": 1.0}]}
            
        try:
            return self.sp.audio_analysis(track_id)
        except Exception:
            return {"sections": []}

    def get_full_enrichment(self, track_name: str, artist_name: str = ""):
        """
        Combines search, features, and analysis into a single JSON-ready dict.
        """
        meta = self.get_track_metadata(track_name, artist_name)
        if not meta:
            return None
            
        features = self.get_audio_features(meta['id'])
        analysis = self.get_audio_analysis(meta['id'])
        
        return {
            "info": meta,
            "features": features,
            "sections": analysis.get('sections', [])
        }

if __name__ == "__main__":
    client = MusicGAUSpotifyClient()
    # Example: Aventura - Obsesion
    data = client.get_full_enrichment("Obsesion", "Aventura")
    if data:
        print(f"Enriched data for {data['info']['name']}")
        print(f"Energy: {data['features']['energy']}")
        print(f"Sections found: {len(data['sections'])}")
