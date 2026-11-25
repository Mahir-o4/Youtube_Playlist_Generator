"""Streamlit entrypoint: uv run streamlit run app.py."""

from __future__ import annotations

import streamlit as st

from components.input_form import render_input_form
from components.results import render_breakdown, render_downloads
from graph.workflow import build_workflow
from schemas import SyllabusBreakdown
from services.llm import DEFAULT_MODEL, has_api_key

st.set_page_config(
    page_title="Syllabus to searchable units",
    page_icon="📚",
    layout="wide",
)


@st.cache_resource(show_spinner=False)
def get_workflow():
    return build_workflow()


st.title("Syllabus → searchable YouTube units")
st.write(
    "Paste a syllabus module to get topics, learning units, checklists, and "
    "ready-to-use YouTube search queries."
)

if not has_api_key():
    st.error(
        "Gemini API key missing. Add `GOOGLE_API_KEY` to the repo's `.env` file "
        "or set it in the environment."
    )

submitted, values = render_input_form()

if submitted:
    if not values["subject"].strip() or not values["syllabus"].strip():
        st.warning("Enter both a subject and some syllabus text.")
    else:
        with st.spinner(f"Decomposing with {DEFAULT_MODEL}..."):
            result = get_workflow().invoke(values)
        if result.get("error"):
            st.error(result["error"])
            st.session_state.pop("breakdown", None)
            st.session_state.pop("finalists", None)
            st.session_state.pop("playlist", None)
            st.session_state.pop("coverage", None)
        else:
            st.session_state["breakdown"] = result["breakdown"]
            st.session_state["finalists"] = result.get("finalists", {})
            st.session_state["playlist"] = result.get("playlist", [])
            st.session_state["coverage"] = result.get("coverage")

breakdown = st.session_state.get("breakdown")
if isinstance(breakdown, SyllabusBreakdown):
    playlist = st.session_state.get("playlist", [])
    render_breakdown(
        breakdown,
        finalists=st.session_state.get("finalists", {}),
        playlist=playlist,
        coverage=st.session_state.get("coverage"),
    )
    render_downloads(breakdown, playlist)
