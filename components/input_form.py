"""Streamlit input form component (compact)."""

from __future__ import annotations

import streamlit as st

LEVELS = ("Undergraduate", "Postgraduate", "High school", "Vocational", "Other")


def render_input_form() -> tuple[bool, dict[str, str]]:
    """Render the syllabus form and return (submitted, values)."""
    with st.form("syllabus_form", border=True):
        subject_col, level_col = st.columns([3, 1])
        with subject_col:
            subject = st.text_input("Subject", placeholder="Linear Algebra")
        with level_col:
            level = st.selectbox("Academic level", LEVELS)
        syllabus = st.text_area(
            "Syllabus module",
            height=120,
            placeholder="Week 1: vectors, vector addition and dot products...",
        )
        submitted = st.form_submit_button("Decompose syllabus", type="primary")

    return submitted, {
        "subject": subject,
        "level": level,
        "syllabus": syllabus,
    }
