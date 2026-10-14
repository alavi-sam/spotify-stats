import altair as alt
import streamlit as st

from data import query
from theme import colors

c = colors()
st.title("Genres")
st.caption("Genres come from Deezer, per album. A play counts once for every genre of its album, "
           "so genre totals add up to more than total plays.")

# top 7 named genres keep a fixed color; everything else (including 'Unknown') folds into Other
top = query("""
    select genre from agg_daily_genre_plays
    where genre <> 'Unknown'
    group by genre
    order by sum(play_count) desc, genre
    limit 7
""")["genre"].tolist()
domain = top + ["Other"]
palette = alt.Scale(domain=domain, range=c["categorical"][:len(top)] + [c["other"]])

# --- weekly mix -----------------------------------------------------------------
st.subheader("Weekly genre mix")
weekly = query("""
    select
        date_trunc('week', play_date_local) as week,
        case when genre in (select unnest(?)) then genre else 'Other' end as genre_group,
        sum(play_count) as plays
    from agg_daily_genre_plays
    group by 1, 2
""", (top,))
weekly["share"] = weekly["plays"] / weekly.groupby("week")["plays"].transform("sum")
weekly = weekly.sort_values("week")
weekly["week_label"] = weekly["week"].dt.strftime("%b %-d")
weekly["stack_order"] = weekly["genre_group"].map({g: i for i, g in enumerate(domain)})

mix = alt.Chart(weekly).mark_bar(stroke=c["surface"], strokeWidth=2, width=alt.RelativeBandSize(0.7)).encode(
    x=alt.X("week_label:O", title="Week of", sort=weekly["week_label"].unique().tolist(), axis=alt.Axis(labelAngle=0)),
    y=alt.Y("plays:Q", stack="normalize", title="Share of genre plays", axis=alt.Axis(format="%")),
    color=alt.Color("genre_group:N", scale=palette, legend=alt.Legend(title=None, orient="bottom", columns=2)),
    order=alt.Order("stack_order:Q"),
    tooltip=[alt.Tooltip("week:T", title="Week of", format="%b %-d"), alt.Tooltip("genre_group:N", title="Genre"),
             alt.Tooltip("plays:Q", title="Plays"), alt.Tooltip("share:Q", title="Share", format=".0%")],
).properties(height=460)
st.altair_chart(mix, width="stretch")
st.caption("The first and current weeks are partial.")

# --- all-time ranking -------------------------------------------------------------
st.subheader("Top genres, all time")
ranking = query("""
    select genre, sum(play_count) as plays, count(distinct play_date_local) as days
    from agg_daily_genre_plays
    group by genre
    order by plays desc, genre
    limit 15
""")
ranking["genre_group"] = ranking["genre"].where(ranking["genre"].isin(top), "Other")
bars = alt.Chart(ranking).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
    x=alt.X("plays:Q", title="Plays", axis=alt.Axis(tickCount=8)),
    y=alt.Y("genre:N", sort="-x", title=None),
    color=alt.Color("genre_group:N", scale=palette, legend=None),
    tooltip=[alt.Tooltip("genre:N", title="Genre"), alt.Tooltip("plays:Q", title="Plays"),
             alt.Tooltip("days:Q", title="Days listened")],
).properties(height=30 * len(ranking))
st.altair_chart(bars, width="stretch")
