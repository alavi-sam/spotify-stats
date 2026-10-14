with daily as (
    select
        play_date_local,
        main_artist_id,
        count(*)                                    as play_count,
        round(sum(duration_ms) / 60000.0, 1)        as est_minutes_played,
        count(distinct track_id)                    as distinct_tracks
    from {{ ref('fct_plays') }}
    group by play_date_local, main_artist_id
)

select
    daily.play_date_local,
    daily.main_artist_id as artist_id,
    ar.artist_name,
    daily.play_count,
    daily.est_minutes_played,
    daily.distinct_tracks
from daily
left join {{ ref('dim_artist') }} as ar on ar.artist_id = daily.main_artist_id
