import requests
from dotenv import load_dotenv
load_dotenv()
import os



def get_access_token():
    url = "https://accounts.spotify.com/api/token"
    res = requests.post(
        url=url,
        data={
            'grant_type': 'refresh_token',
            'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
            'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
            'refresh_token': os.getenv('SPOTIFY_REFRESH_TOKEN'),
            # 'redirect_uri': 'http://127.0.0.1:8888/callback'
        },
        headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )

    return res.json()


def get_recently_played():
    access_token = get_access_token()['access_token']
    response = requests.get(
        url='https://api.spotify.com/v1/audio-features',
        headers={
            'Authorization': f'Bearer {access_token}'
        }
    )

    return response.json()

def get_sound_feature(track_id):
    access_token = get_access_token()['access_token']
    response = requests.get(
        url=f'https://api.spotify.com/v1/audio-features/{track_id}',
        headers={
            'Authorization': f'Bearer {access_token}'
        }
    )

    return response.json()

print(get_sound_feature('44gVkVOtHNR09gDuCftTEq'))