import json
import boto3
import requests
import os
from datetime import datetime, timezone

ssm_client = boto3.client('ssm')
s3_client = boto3.client('s3')


class SpotifyAuthError(Exception):
    pass

class SpotifyAPIError(Exception):
    pass

def get_parameter(name, is_secure=False):
    parameter = ssm_client.get_parameter(Name=os.getenv('SSM_PREFIX') + name, WithDecryption=is_secure)
    return parameter["Parameter"]["Value"]

def update_parameter(name, value, is_secure=False):
    if is_secure:
        ssm_client.put_parameter(
            Name=os.getenv('SSM_PREFIX') + name,
            Overwrite=True,
            Value=value,
            Type='SecureString'
        )
    else:
        ssm_client.put_parameter(
            Name=os.getenv('SSM_PREFIX') + name,
            Overwrite=True,
            Value=value,
        )

def lambda_handler(event, context):
    def get_refresh_token():
        url = "https://accounts.spotify.com/api/token"
        res = requests.post(
            url=url,
            data={
                'grant_type': 'refresh_token',
                'client_id': get_parameter('/client_id', is_secure=True),
                'client_secret': get_parameter('/client_secret', is_secure=True),
                'refresh_token': get_parameter('/refresh_token', is_secure=True)
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        if res.status_code >= 400:
            raise SpotifyAuthError(f"Authorization Error! status_code: {res.status_code}")

        return res.json() 

    def get_recently_played():
        res = get_refresh_token()

        if 'refresh_token' in res:
            update_parameter('/refresh_token', res['refresh_token'], is_secure=True)

        access_token = res['access_token']

        response = requests.get(
            url=f'https://api.spotify.com/v1/me/player/recently-played',
            headers={
                'Authorization': f'Bearer {access_token}'
            },
            params={
                'limit': 50,
                'after': get_parameter('/cursor')
            }
        )
        
        if response.status_code >= 400:
            raise SpotifyAuthError(f"Authorization Error! status_code: {response.status_code}")

        return response.json()

    def put_item(object):
        dt = object['played_at'].split('T')[0]
        unix = datetime.fromisoformat(object['played_at']).replace(tzinfo=timezone.utc)
        unix = int(unix.timestamp() * 1000)

        s3_client.put_object(
            Bucket=os.getenv('RAW_BUCKET'),
            Key=os.getenv('RAW_PREFIX') + f'/dt={dt}/{unix}.json',
            Body=json.dumps(object)
        )

    res = get_recently_played()

    count = 0

    for item in res['items']:
        put_item(item)
        count += 1

    if res.get('cursors'):
            update_parameter('/cursor', res['cursors']['after'])

    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps(f'Added {count} items')
    }
