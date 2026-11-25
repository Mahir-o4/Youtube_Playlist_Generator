"""Streamlit entrypoint: uv run streamlit run app.py."""

from __future__ import annotations

import streamlit as st

from components.input_form import render_input_form
from components.results import render_breakdown, render_download
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
        else:
            st.session_state["breakdown"] = result["breakdown"]

breakdown = st.session_state.get("breakdown")
if isinstance(breakdown, SyllabusBreakdown):
    render_breakdown(breakdown)
    render_download(breakdown)
