with album_artist as (
    SELECT
        artist_id,
        artist_name,
        artist_type,
        artist_url
    from {{ ref('stg_spotify__album_artists') }}
),

track_artist as (
    SELECT
        artist_id,
        artist_name,
        artist_type,
        artist_url
    from {{ ref('stg_spotify__track_artists') }}
)

select * from album_artist 
UNION 
SELECT * from track_artist