"""Streamlit adapter for the advanced orbital lab."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from orbital_dynamics import DEFAULTS
from scenario_workspace import build_workspace, validate_workspace

_component = components.declare_component("orbit_lab", path=str(Path(__file__).parent / "orbit_ui"))


def render():
    st.set_page_config(page_title="태양계 WHAT IF 실험실", page_icon="✳", layout="wide", initial_sidebar_state="collapsed")
    st.markdown("""<style>
        html, body, .stApp, [data-testid="stAppViewContainer"] {background:#080c12!important}
        [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {display:none}
        .block-container {padding:0!important;max-width:100%!important}
        [data-testid="stAppViewContainer"] {padding:0!important}
        [data-testid="stElementContainer"] {margin:0!important}
        [data-testid="stVerticalBlock"] {gap:0!important}
        iframe {display:block;border:0;color-scheme:dark}
    </style>""", unsafe_allow_html=True)
    settings = st.session_state.get("orbit_settings", dict(DEFAULTS))
    request_id = st.session_state.get("orbit_request_id", 0)
    payload = {**build_workspace(settings), "request_id": request_id}
    event = _component(experiment=payload, key="orbit_workspace", default=None)
    if isinstance(event, dict) and (event.get("settings") != settings or event.get("request_id", 0) != request_id):
        try:
            st.session_state.orbit_settings = validate_workspace(event.get("settings"))
            next_id = event.get("request_id", 0)
            if isinstance(next_id, int) and not isinstance(next_id, bool) and next_id >= 0:
                st.session_state.orbit_request_id = next_id
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
