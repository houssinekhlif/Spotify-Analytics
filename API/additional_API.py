import requests
import base64
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# -----------------------------
# Get Spotify API access token
# -----------------------------
def get_access_token(env_path=".env"):
    load_dotenv(Path(env_path))
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# -----------------------------
# Fetch playlist tracks
# -----------------------------
def get_playlist(token, playlist_ids):
    os.makedirs("playlists_json", exist_ok=True)

    for name, pid in playlist_ids.items():
        url = f"https://api.spotify.com/v1/playlists/{pid}/tracks?limit=100"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f" Failed to fetch {name} (Status {response.status_code})")
            continue

        data = response.json()
        tracks = []

        for item in data.get("items", []):
            track = item.get("track")
            if not track:
                continue

            tracks.append({
                "track_id": track.get("id"),
                "track_name": track.get("name"),
                "popularity_score": track.get("popularity"),
                "artists": [a["name"] for a in track.get("artists", [])],
                "artist_ids": [a["id"] for a in track.get("artists", [])]
            })

        file_path = f"playlists_json/{name.replace(' ', '_')}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tracks, f, indent=2, ensure_ascii=False)

        print(f"Playlist {name} saved to {file_path}")

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    token = get_access_token(".env")
    # Example: fetch only Top 50 Global for testing
    playlist_ids = {"Top 50 Arabic": "37i9dQZF1DXdVyc8LtLi96"}
    get_playlist(token, playlist_ids)
