with source as(
    SELECT
    track.album as album
    from {{ source('spotify_raw', 'recently_played') }}
    where track.id not in (select track_id from {{ ref('excluded_tracks') }})
),

album_artist as (
    SELECT
        distinct
        album.id as album_id,
        artist.id as artist_id,
        artist_index as artist_position,
        artist.name  as artist_name,
        artist.type as artist_type,
        element_at(artist.external_urls, 'spotify') as artist_url
    from SOURCE
    cross join unnest(album.artists)
    with ordinality as t(artist, artist_index)
)

select * from album_artist