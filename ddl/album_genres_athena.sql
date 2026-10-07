CREATE EXTERNAL TABLE if not exists deezer_raw.album_genres (
    album_id string,
    status string,
    genres array<string>,
    deezer_album_id bigint,
    fetched_at string
)

partitioned by (dt string)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
location 's3://spotify-listening-history-767397767318-us-east-1-an/raw/deezer/albums/'
tblproperties(
    'projection.enabled' = 'true',
    'projection.dt.type' = 'date',
    'projection.dt.format' = 'yyyy-MM-dd',
    'projection.dt.range' = '2026-10-01,NOW',
    'storage.location.template' = 's3://spotify-listening-history-767397767318-us-east-1-an/raw/deezer/albums/dt=${dt}/'
)
