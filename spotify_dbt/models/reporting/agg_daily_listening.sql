with plays as (
    select * from {{ ref('fct_plays') }}
),

dates as (
    select *
    from {{ ref('dim_date') }}
    where date_day between (select min(play_date_local) from plays)
                       and cast(current_timestamp at time zone 'America/Toronto' as date)
),

daily as (
    select
        play_date_local,
        count(*)                                    as play_count,
        round(sum(duration_ms) / 60000.0, 1)        as est_minutes_played,
        count(distinct track_id)                    as distinct_tracks,
        count(distinct main_artist_id)              as distinct_artists,
        count(distinct album_id)                    as distinct_albums,
        cast(min(played_at_local) as timestamp(3)) as first_play_at,
        cast(max(played_at_local) as timestamp(3)) as last_play_at
    from plays
    group by play_date_local
),

first_plays as (
    select
        track_id,
        min(play_date_local) as first_play_date
    from plays
    group by track_id
),

new_tracks as (
    select
        first_play_date,
        count(*) as new_tracks
    from first_plays
    group by first_play_date
)

select
    d.date_day,
    d.year,
    d.month,
    d.month_name,
    d.day_of_week,
    d.day_name,
    d.is_weekend,
    coalesce(daily.play_count, 0)               as play_count,
    coalesce(daily.est_minutes_played, 0)       as est_minutes_played,
    coalesce(daily.distinct_tracks, 0)          as distinct_tracks,
    coalesce(daily.distinct_artists, 0)         as distinct_artists,
    coalesce(daily.distinct_albums, 0)          as distinct_albums,
    coalesce(new_tracks.new_tracks, 0)          as new_tracks,
    daily.first_play_at,
    daily.last_play_at
from dates as d
left join daily on daily.play_date_local = d.date_day
left join new_tracks on new_tracks.first_play_date = d.date_day
