import json
import requests
import boto3
import time
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Attr

athena_client = boto3.client('athena')
output_location = 's3://spotify-listening-history-767397767318-us-east-1-an/athena-results/'
genre_location = 's3://spotify-listening-history-767397767318-us-east-1-an/raw/deezer/'
ssm_client = boto3.client('ssm')

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('spotify-track-enrichment')

s3_client = boto3.client('s3')


def get_pending_items():
    kwargs = {
        'ProjectionExpression': 'album_id',
        'FilterExpression': Attr('album_id').begins_with('album#') & Attr('status').is_in(['completed', 'no_match', 'no_genre']),
    }
    items = []
    while True:
        res = table.scan(**kwargs)
        items.extend(res['Items'])
        if 'LastEvaluatedKey' not in res:
            break
        kwargs['ExclusiveStartKey'] = res['LastEvaluatedKey']
    return [item['album_id'] for item in items]


def get_parameter(name):
    return ssm_client.get_parameter(Name=name, WithDecryption=True)['Parameter']['Value']


query = """
    SELECT
        album_id,
        min(element_at(track_external_ids, 'isrc')) AS irsc
    FROM spotify_analytics.stg_spotify__plays
    WHERE element_at(track_external_ids, 'isrc') IS NOT NULL
    GROUP BY album_id
"""



def query_database(query):
    res = athena_client.start_query_execution(
        QueryString=query,
        ResultConfiguration={'OutputLocation': output_location}
    )    

    return res['QueryExecutionId']


def get_execution_result(query_execution_id):
    is_success = None
    while is_success != "SUCCEEDED":
        response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        if response['QueryExecution']['Status']['State'] in ("FAILED", "CANCELLED"):
            raise Exception("Athena query failed")
        is_success = response['QueryExecution']['Status']['State']
        time.sleep(0.5)

    return response


def get_query_results(query_execution_id):
    paginator = athena_client.get_paginator('get_query_results')
    rows = []
    for page in paginator.paginate(QueryExecutionId=query_execution_id):
        rows.extend(page['ResultSet']['Rows'])
    return rows

def run_athena_query(query):
    query_id = query_database(query)
    execution_details = get_execution_result(query_id)
    results = get_query_results(execution_details['QueryExecution']['QueryExecutionId'])
    return results


def parse_dictionary(rows):
    keys = [row['VarCharValue'] for row in rows[0]['Data']]
    parsed = []
    for row in rows[1:]:
        parsed.append({keys[i]: row['Data'][i].get('VarCharValue')
         for i in range(len(keys))})

    return parsed


def get_deezer_album_id(track_isrc):
    response = requests.get(f'https://api.deezer.com/track/isrc:{track_isrc}')
    body = response.json()
    if response.status_code != 200 or 'error' in body:
        return None
    return body['album']['id']


def get_album_genre(album_id):
    url = f'https://api.deezer.com/album/{album_id}'
    response = requests.get(url)
    try:
        response.raise_for_status()
        genres = [res['name'] for res in response.json()['genres']['data']]
        return genres
    except Exception:
        return None


def compare_album_ids(athena_results, dynamodb_results):
    athena_album_ids = set([res['album_id'] for res in athena_results])
    dynamo_album_ids = set([res.split("#", 1)[1] for res in dynamodb_results])
    return athena_album_ids - dynamo_album_ids



def request_items(athena_results, album_ids):
    items = list(filter(lambda x: x['album_id'] in album_ids, athena_results))
    for item in items:
        deezer_album_id = get_deezer_album_id(item['irsc'])
        if deezer_album_id is None:
            item['status'] = 'no_match'
            item['genres'] = []
        else:
            genres = get_album_genre(deezer_album_id)
            if genres is None:
                item['status'] = 'error'        # request failed, so retry next run
                item['genres'] = []
            elif not genres:
                item['status'] = 'no_genre'     # album found, but has no genre
                item['genres'] = []
            else:
                item['status'] = 'completed'
                item['genres'] = genres
        item['deezer_album_id'] = deezer_album_id
        time.sleep(0.2)
        yield item



def put_genres(item):
    bucket = 'spotify-listening-history-767397767318-us-east-1-an'

    now = datetime.now(timezone.utc)
    record = {
        'album_id': item['album_id'],
        'genres': item['genres'],
        'status': item['status'],
        'deezer_album_id': item['deezer_album_id'],
        'fetched_at': now.isoformat(),
    }
    s3_client.put_object(
        Bucket=bucket,
        Key=f"raw/deezer/albums/dt={now.strftime('%Y-%m-%d')}/{item['album_id']}.json",
        Body=json.dumps(record),
    )

def lambda_handler(event, context):
    
    
    res = run_athena_query(query)
    rows = parse_dictionary(res)
    albums_pending = get_pending_items()
    album_ids = compare_album_ids(rows, albums_pending)
    tagged_tracks = []
    for item in request_items(rows, album_ids):
        put_genres(item)
        table.put_item(
            Item={
                'album_id': "album#" + item['album_id'],
                'status': item['status'],
                'genres': item['genres'],
                'deezer_album_id': item['deezer_album_id']
            }
        )
        tagged_tracks.append(item['album_id'])
        

    return {
        'statusCode': 200,
        'body': tagged_tracks
    }
