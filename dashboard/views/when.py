import altair as alt
import streamlit as st

from data import query
from theme import colors

c = colors()
st.title("When I listen")
st.caption("Across the whole history · Toronto local time")

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
# label every 3rd hour so 24 columns still fit on a phone
HOUR_LABEL = ("datum.value % 3 != 0 ? '' : datum.value == 0 ? '12a' : datum.value < 12 ? datum.value + 'a'"
              " : datum.value == 12 ? '12p' : (datum.value - 12) + 'p'")

slots = query("select * from agg_listening_by_weekday_hour")

peak = slots.sort_values(["avg_plays_per_day", "play_count"], ascending=False).iloc[0]
hour = int(peak["hour_of_day"])
st.markdown(f"Busiest slot: **{peak['day_name']}s around {hour % 12 or 12} {'am' if hour < 12 else 'pm'}**, "
            f"{peak['avg_plays_per_day']:.1f} plays on an average {peak['day_name']}.")

# --- weekday x hour heatmap -----------------------------------------------------
st.subheader("Average plays by weekday and hour")
heatmap = alt.Chart(slots).mark_rect(cornerRadius=3, stroke=c["surface"], strokeWidth=2).encode(
    x=alt.X("hour_of_day:O", title=None, axis=alt.Axis(labelExpr=HOUR_LABEL, labelAngle=0)),
    y=alt.Y("day_name:N", sort=WEEKDAYS, title=None, axis=alt.Axis(labelExpr="slice(datum.value, 0, 3)")),
    color=alt.Color("avg_plays_per_day:Q", scale=alt.Scale(range=c["sequential"]),
                    legend=alt.Legend(title="Avg plays", orient="top", gradientLength=160)),
    tooltip=[alt.Tooltip("day_name:N", title="Day"), alt.Tooltip("hour_of_day:O", title="Hour (0–23)"),
             alt.Tooltip("avg_plays_per_day:Q", title="Avg plays", format=".2f"),
             alt.Tooltip("play_count:Q", title="Total plays")],
).properties(height=300)
st.altair_chart(heatmap, width="stretch")

# --- by hour of day -------------------------------------------------------------
st.subheader("Average plays by hour of day")
by_hour = query("""
    select hour_of_day,
           round(sum(play_count) / (select sum(weekday_occurrences) from (
               select distinct day_of_week, weekday_occurrences from agg_listening_by_weekday_hour)), 2) as avg_plays
    from agg_listening_by_weekday_hour
    group by hour_of_day
""")
bars = alt.Chart(by_hour).mark_bar(color=c["accent"], cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
    x=alt.X("hour_of_day:O", title=None, axis=alt.Axis(labelExpr=HOUR_LABEL, labelAngle=0)),
    y=alt.Y("avg_plays:Q", title="Avg plays per day"),
    tooltip=[alt.Tooltip("hour_of_day:O", title="Hour (0–23)"), alt.Tooltip("avg_plays:Q", title="Avg plays per day")],
).properties(height=260)
st.altair_chart(bars, width="stretch")
