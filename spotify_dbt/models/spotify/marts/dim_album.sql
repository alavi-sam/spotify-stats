with source as (
    SELECT 
        album_id,
        album_name,
        album_type,
        album_url,
        album_image_url,
        album_image_height,
        album_image_width,
        is_album_playable,
        release_date,
        album_release_date_precision,
        total_tracks
    from {{ ref('stg_spotify__plays') }}
)


select distinct * from source