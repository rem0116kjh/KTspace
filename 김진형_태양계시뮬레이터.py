"""태양계 WHAT IF: 심화 탐구 기본 화면. ?view=classic으로 기본 실험."""
from pathlib import Path
import runpy
import streamlit as st

if st.query_params.get("view") == "classic":
    runpy.run_path(str(Path(__file__).with_name("classic_lab.py")), run_name="__main__")
else:
    from advanced_lab import render
    render()
