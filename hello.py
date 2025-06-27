import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import time

# Load credentials from config.json
with open("config.json") as f:
    config = json.load(f)

client_id = config["spotify_client_id"]
client_secret = config["spotify_client_secret"]

# Set up Spotify API client
auth_manager = SpotifyClientCredentials(client_id, client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager)

def get_playlist_tracks(playlist_id):
    print(f"\nFetching tracks for Playlist ID: {playlist_id}")
    try:
        results = sp.playlist_tracks(playlist_id)
    except Exception as e:
        print("❌ Error fetching playlist:", e)
        return

    tracks = results["items"]
    print(f"Total tracks fetched: {len(tracks)}\n")

    for i, item in enumerate(tracks, start=1):
        track = item["track"]
        name = track.get("name", "Unknown")
        artist = track["artists"][0]["name"] if track.get("artists") else "Unknown"
        preview_url = track.get("preview_url", "No preview")
        print(f"{i}. 🎵 {name} by {artist} | 🔗 Preview: {preview_url}")

# ✅ Test with any playlist ID here (replace with your real ID)
# Remove everything after '?' if you're copying from browser
playlist_id = "6Q7EGijjTgXUlzSjC447Ct"  # Example: Angry English - Rage Beats

get_playlist_tracks(playlist_id)
