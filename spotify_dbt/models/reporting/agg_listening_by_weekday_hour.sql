with plays as (
    select * from {{ ref('fct_plays') }}
),

-- every weekday x hour slot, so empty slots show up as zeros
weekdays as (
    select distinct day_of_week, day_name from {{ ref('dim_date') }}
),

hours as (
    select hour_of_day from unnest(sequence(0, 23)) as t(hour_of_day)
),

-- how many of each weekday the listening history covers, for averages
weekday_occurrences as (
    select
        day_of_week,
        count(*) as weekday_occurrences
    from {{ ref('dim_date') }}
    where date_day between (select min(play_date_local) from plays)
                       and cast(current_timestamp at time zone 'America/Toronto' as date)
    group by day_of_week
),

slot_plays as (
    select
        day_of_week(play_date_local)                as day_of_week,
        hour(played_at_local)                       as hour_of_day,
        count(*)                                    as play_count,
        round(sum(duration_ms) / 60000.0, 1)        as est_minutes_played
    from plays
    group by 1, 2
)

select
    w.day_of_week,
    w.day_name,
    h.hour_of_day,
    coalesce(s.play_count, 0)                   as play_count,
    coalesce(s.est_minutes_played, 0)           as est_minutes_played,
    coalesce(o.weekday_occurrences, 0)          as weekday_occurrences,
    round(cast(coalesce(s.play_count, 0) as double) / nullif(o.weekday_occurrences, 0), 2) as avg_plays_per_day
from weekdays as w
cross join hours as h
left join slot_plays as s on s.day_of_week = w.day_of_week and s.hour_of_day = h.hour_of_day
left join weekday_occurrences as o on o.day_of_week = w.day_of_week
