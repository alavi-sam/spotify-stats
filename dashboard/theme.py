"""Chart colors for light and dark mode (validated reference palette)."""
import streamlit as st

LIGHT = {
    "surface": "#ffffff",           # Streamlit's light background, used for 2px gaps
    "accent": "#2a78d6",            # single-series marks
    "accent_soft": "#86b6ef",       # context marks next to the accent (bars behind a trend)
    "trend": "#184f95",             # line drawn over accent_soft bars
    "other": "#c3c2b7",             # "Other" bucket
    "sequential": ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
    "categorical": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
}

DARK = {
    "surface": "#0e1117",           # Streamlit's dark background
    "accent": "#3987e5",
    "accent_soft": "#1c5cab",
    "trend": "#9ec5f4",
    "other": "#52514e",
    # dark mode: low values recede toward the dark surface, high values glow
    "sequential": ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"],
    "categorical": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
}


def colors() -> dict:
    return DARK if st.context.theme.type == "dark" else LIGHT
