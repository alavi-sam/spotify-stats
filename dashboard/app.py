"""Spotify listening dashboard. Run locally: streamlit run dashboard/app.py"""
import streamlit as st

from data import query

st.set_page_config(page_title="Spotify Listening", page_icon=":material/headphones:", layout="wide")

pages = st.navigation([
    st.Page("views/overview.py", title="Overview", icon=":material/home:", default=True),
    st.Page("views/top.py", title="Top", icon=":material/leaderboard:"),
    st.Page("views/when.py", title="When I listen", icon=":material/schedule:"),
    st.Page("views/genres.py", title="Genres", icon=":material/library_music:"),
])

exported = query("select exported_at_utc from export_info").iloc[0, 0]
st.sidebar.caption(f"Data refreshed daily · last export {exported:%Y-%m-%d %H:%M} UTC")

pages.run()
