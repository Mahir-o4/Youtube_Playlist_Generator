"""Streamlit result rendering components."""

from __future__ import annotations

import json

import streamlit as st

from schemas import SyllabusBreakdown


def render_breakdown(breakdown: SyllabusBreakdown) -> None:
    unit_count = sum(len(topic.units) for topic in breakdown.topics)
    st.success(f"{len(breakdown.topics)} topics · {unit_count} searchable units")

    for topic_index, topic in enumerate(breakdown.topics, start=1):
        with st.expander(f"{topic_index}. {topic.title}", expanded=topic_index == 1):
            st.write(topic.summary)
            for unit_index, unit in enumerate(topic.units, start=1):
                st.subheader(f"{topic_index}.{unit_index} {unit.title}")
                st.caption(unit.objective)
                st.markdown("**Checklist**")
                for item in unit.checklist:
                    st.markdown(f"- [ ] {item.text}")
                st.markdown("**YouTube search**")
                st.code(unit.search_query, language="text")


def render_download(breakdown: SyllabusBreakdown) -> None:
    st.download_button(
        "Download JSON",
        data=json.dumps(breakdown.model_dump(), indent=2, ensure_ascii=False),
        file_name="syllabus-breakdown.json",
        mime="application/json",
    )
