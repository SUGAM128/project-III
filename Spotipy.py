import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time
import json
import os

with open('config.json') as config_file:
    config = json.load(config_file)
client_id = config['spotify_client_id']
client_secret = config['spotify_client_secret']

auth_manager = SpotifyClientCredentials(client_id, client_secret)
sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=15)

def getTrackIDs(playlist_id):
    track_ids = []
    playlist = sp.playlist(playlist_id)
    for item in playlist["tracks"]["items"]:
        track = item["track"]
        if track and track["id"]:
            track_ids.append(track["id"])
    return track_ids

def getTrackFeatures(track_id, language_label, retries=3, delay=2):
    for attempt in range(retries):
        try:
            track_info = sp.track(track_id)
            name = track_info.get("name") or "null"
            album = track_info.get("album", {}).get("name") or "null"
            artists = track_info.get("artists", [])
            artist = artists[0]["name"] if artists else "null"
            images = track_info.get("album", {}).get("images", [])
            image = images[0]["url"] if images else "null"
            preview_url = track_info.get("preview_url") or "null"
            available_markets = track_info.get("available_markets", [])
            spotify_url = track_info.get("external_urls", {}).get("spotify", "null")

            return [name, album, artist, preview_url, image, language_label, spotify_url]

        except Exception as e:
            print(f"Error fetching track {track_id} (Attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay)

    return ["null"] * 7

emotion_dict = {
    0: "Angry",
    1: "Disgusted",
    2: "Fearful",
    3: "Happy",
    4: "Neutral",
    5: "Sad",
    6: "Surprised",
}

music_dist = {
    0: {
        "Hindi": "5cwtgqs4L1fX8IKoQebfjJ",
        "Nepali": "3USaR7NzbbweARnqxLn5Qt",
        "English": "6Q7EGijjTgXUlzSjC447Ct"
    },
    1: {
        "Hindi": "6oi4AMa8S7ijiQbRyTk94c",
        "Nepali": "4Boop6WQfDfY7Z5J3te0Th",
        "English": "34xz5XBJchlf3U4zWcUhVj"
    },
    2: {
        "Hindi": "02uXGKglrYZD67gcyxkvTd",
        "Nepali": "0ocZPqOkbGzOoRYWlmtfk7",
        "English": "1NIlouPwHi81SPIfHf213T"
    },
    3: {
        "Hindi": "1Dk9SeguLL5qTnjfyX5VnZ",
        "Nepali": "2Y5Wuz5T5BHkbtyqUcGZFI",
        "English": "5jrWcIQAYqrx8vrYFVLpO8"
    },
    4: {
        "Hindi": "6Ail4atkMPnFdPpAMVcbJ8",
        "Nepali": "2JDjfe77ac6FCUD4urKbaq",
        "English": "2aod9Xs0wS15ZqzO2YyX20"
    },
    5: {
        "Hindi": "189Sow1xr7R94oSKs4kISc",
        "Nepali": "0cJ47XzuYwO0BWu0refX2g",
        "English": "25ZzkJkOuYir9kHr2CqwPQ"
    },
    6: {
        "Hindi": "7vatYrf39uVaZ8G2cVtEik",
        "Nepali": "5OBsjyDS8VHlCd54IkIOvB",
        "English": "2GVQ4nV38EST4pzbAibxOA"
    },
}

os.makedirs("songs", exist_ok=True)

def fetch_save_playlist_by_emotion_language(emotion_key, language, playlist_id):
    print(f"Fetching playlist for Emotion: {emotion_dict[emotion_key]}, Language: {language}")
    track_ids = getTrackIDs(playlist_id)
    track_list = []
    for i, track_id in enumerate(track_ids):
        time.sleep(0.3)
        track_data = getTrackFeatures(track_id, language)
        if "null" in track_data[:3]:
            continue
        track_list.append(track_data)
        print(f"  Fetched {i+1}/{len(track_ids)}: {track_data[0]} -> {track_data[-1]}")
    return track_list

def main():
    print("Select a mood to fetch playlist:")
    for key, mood in emotion_dict.items():
        print(f"{key}: {mood}")

    try:
        choice = int(input("Enter the number corresponding to the mood: "))
        if choice not in emotion_dict:
            print("Invalid choice. Exiting.")
            return
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    all_tracks_for_emotion = []
    for language, playlist_id in music_dist[choice].items():
        tracks = fetch_save_playlist_by_emotion_language(choice, language, playlist_id)
        all_tracks_for_emotion.extend(tracks)

    df = pd.DataFrame(
        all_tracks_for_emotion,
        columns=["Name", "Album", "Artist", "PreviewURL", "Image", "Language", "SpotifyURL"],
    )
    csv_path = f"songs/{emotion_dict[choice].lower()}.csv"
    df.to_csv(csv_path, index=False)
    print(f"Combined CSV saved for emotion '{emotion_dict[choice]}' at: {csv_path}\n")

if __name__ == "__main__":
    main()
