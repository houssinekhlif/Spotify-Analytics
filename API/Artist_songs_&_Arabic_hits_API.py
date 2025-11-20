import requests
import base64
import json
from dotenv import load_dotenv
import os
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')


# -------------------- AUTH --------------------
def get_access_token(env_vars_path):
    """Get a Spotify API access token."""
    dotenv_path = Path(env_vars_path)
    load_dotenv(dotenv_path=dotenv_path)
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")

    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    token_url = "https://accounts.spotify.com/api/token"
    data = {"grant_type": "client_credentials"}
    headers = {
        "Authorization": f"Basic {b64_auth_str}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(token_url, data=data, headers=headers)
    json_result = json.loads(response.content)
    return json_result["access_token"]


# -------------------- ARTIST TRACK EXTRACTION --------------------
def get_artist_id(token, artist_name):
    """Get artist Spotify ID from name."""
    url = f"https://api.spotify.com/v1/search?q={artist_name}&type=artist&limit=1"
    headers = {"Authorization": f"Bearer {token}"}
    result = requests.get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result["artists"]["items"][0]["id"]


def get_artist_albums(token, artist_id):
    """Get all albums of an artist."""
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?limit=50&include_groups=album,single"
    headers = {"Authorization": f"Bearer {token}"}
    result = requests.get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result["items"]


def create_album_name_to_id_dict(album_items):
    """Map album names to their IDs."""
    return {item["name"]: item["id"] for item in album_items}


def get_album_songs(album_id, token):
    """Get all songs in an album."""
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks?limit=50"
    headers = {"Authorization": f"Bearer {token}"}
    result = requests.get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result["items"]


def get_track_details(track_id, token):
    """Get detailed info for a track (popularity, duration, etc)."""
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {"Authorization": f"Bearer {token}"}
    result = requests.get(url, headers=headers)
    if result.status_code == 200:
        json_result = json.loads(result.content)
        return {
            "id": json_result["id"],
            "name": json_result["name"],
            "popularity": json_result["popularity"],
            "duration_ms": json_result["duration_ms"],
            "explicit": json_result["explicit"],
            "preview_url": json_result.get("preview_url"),
            "album_name": json_result["album"]["name"],
            "release_date": json_result["album"]["release_date"]
        }
    return None


def create_albums_tracks_data(token, albums):
    """Create nested dict of albums -> tracks -> track details."""
    albums_data = {}
    for album_name, album_id in albums.items():
        print(f"🎧 Fetching tracks for album: {album_name}")
        album_tracks = get_album_songs(album_id, token)
        track_data_dict = {}

        for track in album_tracks:
            track_id = track["id"]
            details = get_track_details(track_id, token)
            if details:
                track_data_dict[track["name"]] = details

        albums_data[album_name] = track_data_dict

    return albums_data


def get_playlist(token, playlist_ids):
    for name, pid in playlist_ids.items():
        url = f"https://api.spotify.com/v1/playlists/{pid}/tracks?limit=100"
        headers = {"Authorization": "Bearer " + token}
        tracks = []

        while url:
            response = requests.get(url, headers=headers)
            data = response.json()

            if "items" not in data:
                print(f"⚠️ Failed to fetch {name}")
                break

            for item in data["items"]:
                track = item.get("track")
                if not track:
                    continue  # skip unavailable tracks
                tracks.append({
                    "track_id": track.get("id"),
                    "track_name": track.get("name"),
                    "popularity_score": track.get("popularity"),
                    "artist_name": [a["name"] for a in track.get("artists", [])],
                    "artist_id": [a["id"] for a in track.get("artists", [])]
                })

            url = data.get("next")  # for pagination

        file_path = f"playlists_json/{name.replace(' ', '_')}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tracks, f, indent=2, ensure_ascii=False)

        print(f"✅ Playlist {name} saved to {file_path}")





# -------------------- MAIN --------------------
def main():
    access_token = get_access_token(".env")

    # --- Artist Extraction ---
    artist_name = "NF"
    print(f"\n🎤 Fetching all tracks for {artist_name}...")
    artist_id = get_artist_id(access_token, artist_name)
    albums = create_album_name_to_id_dict(get_artist_albums(access_token, artist_id))
    albums_tracks_data = create_albums_tracks_data(access_token, albums)

    artist_file = f"{artist_name.lower().replace(' ', '_')}_tracks.json"
    with open(artist_file, "w", encoding="utf-8") as f:
        json.dump(albums_tracks_data, f, indent=2, ensure_ascii=False)
    print(f"✅ All tracks with details saved to '{artist_file}'!")

    # --- Playlists Extraction ---
    print("\n🎵 Fetching Top 50 playlists from multiple regions...")
    os.makedirs("playlists_json", exist_ok=True)
    playlist_ids = {
        "Top 50 Global": "37i9dQZEVXbMDoHDwVN2tF",
        "Top 50 USA": "37i9dQZEVXbLRQDuF5jeBp",
        "Top 50 France": "37i9dQZEVXbIPWwFssbupI",
        "Top 50 Germany": "37i9dQZEVXbJiZcmkrIHGU",
        "Top 50 Brazil": "37i9dQZEVXbMXbN3EUUhlg",
        "Top 50 India": "37i9dQZEVXbLZ52XmnySJg",
        "Top 50 UK": "37i9dQZEVXbLnolsZ8PSNw",
        "Top 50 Canada": "37i9dQZEVXbKj23U1GF4IR",
        "Top 50 Japan": "37i9dQZEVXbKXQ4mDTEBXq",
        "Top 50 Mexico": "37i9dQZEVXbO3qyFxbkOE1",
        "Top 50 Arabic": "37i9dQZF1DXdVyc8LtLi96"
    }
    # get_playlist(access_token, playlist_names)
    get_playlist(access_token, playlist_ids)
    print("\n✅ All playlists saved inside the 'playlists_json/' folder.")

if __name__ == "__main__":
    main()













#UNFORTUNATELY WE CAN NOT EXTRACT AUDIO FEATURES OF THE TRACKS.

# with open('playlist_songs_and_ids.json', 'r',encoding="utf8") as f:
#     data = json.load(f)

# def get_song_data(token,track_id):
#   url = f"https://api.spotify.com/v1/audio-features/{track_id}"
#   headers = {"Authorization": "Bearer " + token}  
#   result = requests.get(url, headers=headers)
#   json_result = json.loads(result.content)
#   return json_result

# # def fill_song_data(data,token):
# #   for key,value in data.items():
# #     get_song_data(token,value)

# json_result=get_song_data(access_token,"48l6xps5kWSsxtYdXHgz0Y")
# print(json_result)
