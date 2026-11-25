"""Streamlit input form component."""

from __future__ import annotations

import streamlit as st

LEVELS = ("Undergraduate", "Postgraduate", "High school", "Vocational", "Other")
LANGUAGES = ("English", "Bengali", "Hindi", "Spanish", "French", "Arabic", "Other")


def render_input_form() -> tuple[bool, dict[str, str]]:
    """Render the syllabus form and return (submitted, values)."""
    with st.form("syllabus_form"):
        subject = st.text_input("Subject", placeholder="Linear Algebra")
        level = st.selectbox("Academic level", LEVELS)
        language = st.selectbox("Preferred language", LANGUAGES)
        syllabus = st.text_area(
            "Syllabus module",
            height=240,
            placeholder="Week 1: vectors, vector addition and dot products...",
        )
        submitted = st.form_submit_button(
            "Decompose syllabus", type="primary", use_container_width=True
        )
    return submitted, {
        "subject": subject,
        "level": level,
        "language": language,
        "syllabus": syllabus,
    }
