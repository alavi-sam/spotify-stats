import altair as alt
import pandas as pd
import streamlit as st

from data import query
from theme import colors

c = colors()
st.title("Overview")

daily = query("select * from agg_daily_listening order by date_day")
latest = daily["date_day"].max()
st.caption(f"Data through {latest:%A, %B %-d, %Y} · times are Toronto local")

# --- last 7 full days vs the 7 before ----------------------------------------
# The export runs early in the morning, so the latest day has barely started;
# the comparison ends at the last complete day instead.
last_full = (latest - pd.Timedelta(days=1)).date()
window = query("""
    select
        case when play_date_local > ?::date - 7 then 'current' else 'previous' end as period,
        count(*)                                as plays,
        round(sum(duration_ms) / 3600000.0, 1)  as hours,
        count(distinct main_artist_id)          as artists
    from rpt_plays_enriched
    where play_date_local > ?::date - 14 and play_date_local <= ?::date
    group by 1
""", (last_full, last_full, last_full)).set_index("period")
new_tracks = query("""
    select
        sum(new_tracks) filter (where date_day > ?::date - 7)   as current,
        sum(new_tracks) filter (where date_day <= ?::date - 7)  as previous
    from agg_daily_listening
    where date_day > ?::date - 14 and date_day <= ?::date
""", (last_full, last_full, last_full, last_full)).iloc[0]


def kpi(col, label, current, previous, fmt="{:,.0f}", help=None):
    current = 0 if pd.isna(current) else current
    delta = None if pd.isna(previous) else fmt.format(current - previous)
    # neutral delta color: listening less isn't "bad"
    col.metric(label, fmt.format(current), delta, delta_color="off", border=True, help=help)


first_full = last_full - pd.Timedelta(days=6)
st.subheader("Last 7 days", help="The last 7 complete days, compared with the 7 days before. "
                                 "Today is left out because it's still in progress.")
st.caption(f"{first_full:%b %-d} – {last_full:%b %-d}")
k1, k2, k3, k4 = st.columns(4)
for col, label, field, fmt, help in [
    (k1, "Plays", "plays", "{:,.0f}", None),
    (k2, "Est. hours", "hours", "{:,.1f}", "Sum of full track lengths; Spotify doesn't report time actually listened."),
    (k3, "Artists", "artists", "{:,.0f}", None),
]:
    kpi(col, label, window[field].get("current"), window[field].get("previous"), fmt, help)
kpi(k4, "New tracks", new_tracks["current"], new_tracks["previous"],
    help="Tracks played for the first time ever.")

# --- daily plays with 7-day average -----------------------------------------
st.subheader("Plays per day")
daily["avg_7d"] = daily["play_count"].rolling(7, min_periods=1).mean().round(1)
series = alt.Scale(domain=["Daily plays", "7-day average"], range=[c["accent_soft"], c["trend"]])
base = alt.Chart(daily).encode(
    x=alt.X("yearmonthdate(date_day):T", title=None, axis=alt.Axis(format="%b %-d", labelOverlap=True)))
bars = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, width=alt.RelativeBandSize(0.8)).encode(
    y=alt.Y("play_count:Q", title="Plays"),
    color=alt.Color("series:N", scale=series, legend=alt.Legend(title=None, orient="top")),
    tooltip=[alt.Tooltip("date_day:T", title="Date", format="%a %b %-d"),
             alt.Tooltip("play_count:Q", title="Plays"),
             alt.Tooltip("est_minutes_played:Q", title="Est. minutes"),
             alt.Tooltip("distinct_tracks:Q", title="Different tracks")],
).transform_calculate(series="'Daily plays'")
line = base.mark_line(strokeWidth=2).encode(
    x=alt.X("yearmonthdate(date_day):T", bandPosition=0.5),
    y="avg_7d:Q",
    color=alt.Color("series:N", scale=series),
    tooltip=[alt.Tooltip("date_day:T", title="Date", format="%a %b %-d"),
             alt.Tooltip("avg_7d:Q", title="7-day average")],
).transform_calculate(series="'7-day average'")
st.altair_chart((bars + line).properties(height=320), width="stretch")

# --- recent plays -------------------------------------------------------------
st.subheader("Recently played")
recent = query("""
    select album_image_url, played_at_local, track_name, all_artist_names, album_name
    from rpt_plays_enriched order by played_at_local desc limit 15
""")
st.dataframe(
    recent, hide_index=True, width="stretch",
    column_config={
        "album_image_url": st.column_config.ImageColumn("", width="small"),
        "played_at_local": st.column_config.DatetimeColumn("Played at", format="MMM D, h:mm a"),
        "track_name": "Track", "all_artist_names": "Artists", "album_name": "Album",
    },
)
