with source as (select 
    *
from {{ source('spotify_raw', 'recently_played') }}
),

local_time as (
    SELECT
        *,
        cast(from_iso8601_timestamp(played_at) at time zone 'America/Toronto' as timestamp) as local_play_time,
        cast(to_unixtime(from_iso8601_timestamp(played_at) at time zone 'America/Toronto') * 1000 as bigint) as play_id
        
    FROM source
),  
unnested as (
    select
        track.album.album_type,
        track.album.name as album_name,
        track.album.artists as album_artists,
        track.album.href as album_url,
        track.album.id as album_id,
        track.album.images[1].url as album_image_url,
        track.album.images[1].width as album_image_width,
        track.album.images[1].height as album_image_height,
        track.album.is_playable as is_album_playable,
        track.album.release_date,
        track.album.release_date_precision as album_release_date_precision,
        track.album.total_tracks as total_tracks,
        track.artists,
        track.disc_number as track_disc_number,
        track.duration_ms,
        track.explicit,
        track.external_ids as track_external_ids,
        track.external_urls as track_external_urls,
        track.href as track_url,
        track.id as track_id,
        track.is_local as is_track_local,
        track.is_playable as is_track_playable,
        track.name as track_name,
        track.track_number as track_number,
        track.type as track_type,
        cast(format_datetime(from_iso8601_timestamp(played_at) at time zone 'America/Toronto', 'yyyy-MM-dd HH:mm:ss.SSS') as timestamp) as played_at_local,
        cast(from_iso8601_timestamp(played_at) as timestamp) as played_at_utc,
        play_id,
        context as context_type,
        dt as partition_date
    from local_time
)



