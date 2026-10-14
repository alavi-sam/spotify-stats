"""Spotify listening dashboard. Run locally: streamlit run dashboard/app.py"""
import streamlit as st

from data import query

st.set_page_config(page_title="Spotify Listening", page_icon=":material/headphones:", layout="wide")

# (page, short label for the link row; full title shows in the browser tab)
PAGES = [
    (st.Page("views/overview.py", title="Overview", default=True), "Overview"),
    (st.Page("views/top.py", title="Top"), "Top"),
    (st.Page("views/when.py", title="When I listen"), "When"),
    (st.Page("views/genres.py", title="Genres"), "Genres"),
]

# Streamlit's own menu (sidebar or top bar) collapses behind a ">>" button on
# phones, so hide it and draw one row of links that looks the same everywhere.
current = st.navigation([page for page, _ in PAGES], position="hidden")
links = st.container(horizontal=True, gap="small")
for page, label in PAGES:
    links.page_link(page, label=label)

current.run()

exported = query("select exported_at_utc from export_info").iloc[0, 0]
st.divider()
st.caption(f"Data refreshed daily · last export {exported:%Y-%m-%d %H:%M} UTC")
