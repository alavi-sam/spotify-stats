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
history_days = (last_day - first_day).days + 1

# --- period filter ------------------------------------------------------------
# A preset only appears once the history is longer than it; until then it would
# show exactly the same as "All time".
presets = {label: days for label, days in {"7 days": 7, "30 days": 30}.items() if days < history_days}
presets["All time"] = None
default = "30 days" if "30 days" in presets else "All time"

f1, f2 = st.columns([2, 3])
choice = f1.segmented_control("Period", [*presets, "Custom"], default=default) or default
if choice == "Custom":
    picked = f2.date_input("Dates", (max(first_day, last_day - timedelta(days=29)), last_day),
                           min_value=first_day, max_value=last_day)
    start, end = (picked[0], picked[-1]) if picked else (first_day, last_day)
else:
    days = presets[choice]
    start, end = (first_day if days is None else max(first_day, last_day - timedelta(days=days - 1))), last_day
st.caption(f"{start:%b %-d} – {end:%b %-d, %Y}")
period = (start, end)

TOP_N, MAX_ROWS, MIN_PLAYS = 10, 20, 2


def top_with_ties(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """The top TOP_N by plays, keeping everything tied at the cutoff.

    Rows are never dropped just because of their name: if the tie at the cutoff
    would push the list past MAX_ROWS, the whole tied group is left out.
    Single plays don't count as a favourite.
    Returns (rows shown, how many were left out as a tie, their play count).
    """
    df = df[df["plays"] >= MIN_PLAYS].sort_values("plays", ascending=False)
    if df.empty:
        return df, 0, 0
    cutoff = int(df["plays"].iloc[min(TOP_N, len(df)) - 1])
    shown = df[df["plays"] >= cutoff]
    if len(shown) <= MAX_ROWS:
        return shown, 0, cutoff
    return df[df["plays"] > cutoff], int((df["plays"] == cutoff).sum()), cutoff


def show_ranking(df: pd.DataFrame, noun: str, label: str, tooltip: list, table: list, config: dict):
    shown, tied, cutoff = top_with_ties(df)
    if shown.empty:
        st.info(f"{tied} {noun}s are tied at {cutoff} plays, too many to rank. Try a longer period." if tied else
                f"No {noun} was played {MIN_PLAYS}+ times in this period, so there's no ranking yet.")
        return
    caption = f"{len(shown)} {noun}s with {int(shown['plays'].min())}+ plays"
    caption += f" · {tied} more tied at {cutoff} plays" if tied else " · ties at the cutoff are included"
    st.caption(caption)

    chart = alt.Chart(shown).mark_bar(
        color=c["accent"], cornerRadiusTopRight=4, cornerRadiusBottomRight=4,
    ).encode(
        x=alt.X("plays:Q", title="Plays", axis=alt.Axis(tickMinStep=1)),
        y=alt.Y(f"{label}:N", sort="-x", title=None, axis=alt.Axis(labelLimit=150)),
        tooltip=tooltip,
    ).properties(height=max(120, 30 * len(shown)))

    left, right = st.columns([3, 2])
    left.altair_chart(chart, width="stretch")
    right.dataframe(shown[table], hide_index=True, width="stretch", column_config=config)


# Artists first: plays add up across an artist's tracks, so this ranking
# separates out much sooner than tracks, where most plays are one-offs.
artists_tab, tracks_tab, albums_tab = st.tabs(["Artists", "Tracks", "Albums"])

with artists_tab:
    artists = query("""
        select artist_name, sum(play_count) as plays, round(sum(est_minutes_played)) as minutes
        from agg_daily_artist_plays
        where play_date_local between ? and ?
        group by artist_id, artist_name
    """, period)
    show_ranking(
        artists, "artist", "artist_name",
        [alt.Tooltip("artist_name:N", title="Artist"), alt.Tooltip("plays:Q", title="Plays"),
         alt.Tooltip("minutes:Q", title="Est. minutes")],
        ["artist_name", "plays", "minutes"],
        {"artist_name": "Artist", "plays": "Plays", "minutes": "Est. minutes"},
    )
    st.caption("Counts the main (first-credited) artist of each track.")

with tracks_tab:
    tracks = query("""
        select
            track_name || ' — ' || main_artist_name as label,
            track_name, main_artist_name, any_value(album_image_url) as album_image_url,
            count(*) as plays, round(sum(duration_ms) / 60000.0) as minutes
        from rpt_plays_enriched
        where play_date_local between ? and ?
        group by track_id, track_name, main_artist_name
    """, period)
    show_ranking(
        tracks, "track", "label",
        [alt.Tooltip("track_name:N", title="Track"), alt.Tooltip("main_artist_name:N", title="Artist"),
         alt.Tooltip("plays:Q", title="Plays"), alt.Tooltip("minutes:Q", title="Est. minutes")],
        ["album_image_url", "track_name", "main_artist_name", "plays"],
        {"album_image_url": st.column_config.ImageColumn("", width="small"),
         "track_name": "Track", "main_artist_name": "Artist", "plays": "Plays"},
    )

with albums_tab:
    albums = query("""
        select
            album_name || ' — ' || any_value(main_artist_name) as label,
            album_name, any_value(main_artist_name) as artist, any_value(album_image_url) as album_image_url,
            count(*) as plays, count(distinct track_id) as tracks
        from rpt_plays_enriched
        where play_date_local between ? and ?
        group by album_id, album_name
    """, period)
    show_ranking(
        albums, "album", "label",
        [alt.Tooltip("album_name:N", title="Album"), alt.Tooltip("artist:N", title="Artist"),
         alt.Tooltip("plays:Q", title="Plays"), alt.Tooltip("tracks:Q", title="Different tracks")],
        ["album_image_url", "album_name", "artist", "plays"],
        {"album_image_url": st.column_config.ImageColumn("", width="small"),
         "album_name": "Album", "artist": "Artist", "plays": "Plays"},
    )
