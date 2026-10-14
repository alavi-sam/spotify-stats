with daily as (
    select
        play_date_local,
        track_id,
        album_id,
        main_artist_id,
        count(*)                                    as play_count,
        round(sum(duration_ms) / 60000.0, 1)        as est_minutes_played,
        cast(min(played_at_local) as timestamp(3)) as first_played_at,
        cast(max(played_at_local) as timestamp(3)) as last_played_at
    from {{ ref('fct_plays') }}
    group by play_date_local, track_id, album_id, main_artist_id
)

select
    daily.play_date_local,
    daily.track_id,
    t.track_name,
    daily.album_id,
    al.album_name,
    daily.main_artist_id,
    ar.artist_name as main_artist_name,
    daily.play_count,
    daily.est_minutes_played,
    daily.first_played_at,
    daily.last_played_at
from daily
left join {{ ref('dim_track') }} as t on t.track_id = daily.track_id
left join {{ ref('dim_album') }} as al on al.album_id = daily.album_id
left join {{ ref('dim_artist') }} as ar on ar.artist_id = daily.main_artist_id
