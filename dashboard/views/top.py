from datetime import timedelta

import altair as alt
import pandas as pd
import streamlit as st

from data import query
from theme import colors

c = colors()
st.title("Top")

bounds = query("select min(date_day) as lo, max(date_day) as hi from agg_daily_listening").iloc[0]
first_day, last_day = pd.Timestamp(bounds["lo"]).date(), pd.Timestamp(bounds["hi"]).date()

# --- period filter ------------------------------------------------------------
presets = {"7 days": 7, "30 days": 30, "All time": None}
f1, f2 = st.columns([2, 3])
choice = f1.segmented_control("Period", [*presets, "Custom"], default="30 days") or "30 days"
if choice == "Custom":
    picked = f2.date_input("Dates", (max(first_day, last_day - timedelta(days=29)), last_day),
                           min_value=first_day, max_value=last_day)
    start, end = (picked[0], picked[-1]) if picked else (first_day, last_day)
else:
    days = presets[choice]
    start, end = (first_day if days is None else max(first_day, last_day - timedelta(days=days - 1))), last_day
st.caption(f"{start:%b %-d} – {end:%b %-d, %Y}")
period = (start, end)


def ranking(df: pd.DataFrame, label: str, tooltip: list) -> alt.Chart:
    """Horizontal bars, highest first, one hue."""
    return alt.Chart(df).mark_bar(
        color=c["accent"], cornerRadiusTopRight=4, cornerRadiusBottomRight=4,
    ).encode(
        x=alt.X("plays:Q", title="Plays", axis=alt.Axis(tickMinStep=1)),
        y=alt.Y(f"{label}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=150)),
        tooltip=tooltip,
    ).properties(height=max(120, 30 * len(df)))


tracks_tab, artists_tab, albums_tab = st.tabs(["Tracks", "Artists", "Albums"])

with tracks_tab:
    tracks = query("""
        select
            track_name || ' — ' || main_artist_name as label,
            track_name, main_artist_name, any_value(album_image_url) as album_image_url,
            count(*) as plays, round(sum(duration_ms) / 60000.0) as minutes
        from rpt_plays_enriched
        where play_date_local between ? and ?
        group by track_id, track_name, main_artist_name
        order by plays desc, track_name
        limit 10
    """, period)
    left, right = st.columns([3, 2])
    left.altair_chart(ranking(tracks, "label", [
        alt.Tooltip("track_name:N", title="Track"), alt.Tooltip("main_artist_name:N", title="Artist"),
        alt.Tooltip("plays:Q", title="Plays"), alt.Tooltip("minutes:Q", title="Est. minutes")]),
        width="stretch")
    right.dataframe(tracks[["album_image_url", "track_name", "main_artist_name", "plays"]],
                    hide_index=True, width="stretch", column_config={
                        "album_image_url": st.column_config.ImageColumn("", width="small"),
                        "track_name": "Track", "main_artist_name": "Artist", "plays": "Plays"})

with artists_tab:
    artists = query("""
        select artist_name, sum(play_count) as plays, round(sum(est_minutes_played)) as minutes
        from agg_daily_artist_plays
        where play_date_local between ? and ?
        group by artist_id, artist_name
        order by plays desc, artist_name
        limit 10
    """, period)
    left, right = st.columns([3, 2])
    left.altair_chart(ranking(artists, "artist_name", [
        alt.Tooltip("artist_name:N", title="Artist"), alt.Tooltip("plays:Q", title="Plays"),
        alt.Tooltip("minutes:Q", title="Est. minutes")]), width="stretch")
    right.dataframe(artists, hide_index=True, width="stretch",
                    column_config={"artist_name": "Artist", "plays": "Plays", "minutes": "Est. minutes"})
    st.caption("Counts the main (first-credited) artist of each track.")

with albums_tab:
    albums = query("""
        select
            album_name || ' — ' || any_value(main_artist_name) as label,
            album_name, any_value(main_artist_name) as artist, any_value(album_image_url) as album_image_url,
            count(*) as plays, count(distinct track_id) as tracks
        from rpt_plays_enriched
        where play_date_local between ? and ?
        group by album_id, album_name
        order by plays desc, album_name
        limit 10
    """, period)
    left, right = st.columns([3, 2])
    left.altair_chart(ranking(albums, "label", [
        alt.Tooltip("album_name:N", title="Album"), alt.Tooltip("artist:N", title="Artist"),
        alt.Tooltip("plays:Q", title="Plays"), alt.Tooltip("tracks:Q", title="Different tracks")]),
        width="stretch")
    right.dataframe(albums[["album_image_url", "album_name", "artist", "plays"]],
                    hide_index=True, width="stretch", column_config={
                        "album_image_url": st.column_config.ImageColumn("", width="small"),
                        "album_name": "Album", "artist": "Artist", "plays": "Plays"})
