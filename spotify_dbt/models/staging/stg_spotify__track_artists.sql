with source as(
    SELECT
        *
    from {{ source('spotify_raw', 'recently_played') }}
),

track_artist as (
    SELECT
        distinct
        track.id as track_id,
        artist.id as artist_id,
        artist_index as artist_position,
        artist.name as artist_name,
        artist.type as artist_type,
        element_at(artist.external_urls, 'spotify') as artist_url
    from SOURCE
    cross join unnest(track.artists)
    with ordinality as t(artist, artist_index)
)

select * from track_artist