with spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2015-01-01' as date)",
        end_date="date_add('year', 1, current_date)"
    ) }}
),

days as (
    select cast(date_day as date) as date_day
    from spine
)

select
    date_day,
    year(date_day)                                      as year,
    quarter(date_day)                                   as quarter,
    month(date_day)                                     as month,
    date_format(cast(date_day as timestamp), '%M')      as month_name,
    day(date_day)                                       as day_of_month,
    day_of_week(date_day)                               as day_of_week,
    date_format(cast(date_day as timestamp), '%W')      as day_name,
    week_of_year(date_day)                              as week_of_year,
    day_of_week(date_day) in (6, 7)                     as is_weekend
from days