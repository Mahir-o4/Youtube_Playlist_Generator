from __future__ import annotations

from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

import graph.workflow
from schemas import SyllabusBreakdown

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"

BREAKDOWN = {
    "subject": "Linear Algebra",
    "level": "Undergraduate",
    "language": "English",
    "topics": [
        {
            "title": "Vectors",
            "summary": "Vector basics.",
            "units": [
                {
                    "title": "Vector basics",
                    "objective": "Explain vectors.",
                    "checklist": [{"text": "Define a vector."}],
                    "search_query": "undergraduate linear algebra vectors",
                }
            ],
        }
    ],
}


def test_ui_renders_without_api_call(monkeypatch) -> None:
    class FakeGraph:
        def invoke(self, state: dict) -> dict:
            return {
                "breakdown": SyllabusBreakdown.model_validate(BREAKDOWN),
                "error": None,
            }

    monkeypatch.setattr(graph.workflow, "build_workflow", lambda: FakeGraph())
    st.cache_resource.clear()

    at = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    at.text_input[0].set_value("Linear Algebra")
    at.text_area[0].set_value("Week 1: vectors and vector addition.")
    at.form[0].form_submit_button[0].click().run()

    assert not at.exception
    assert "1 topics · 1 searchable units" in [m.value for m in at.success]
    assert [b.label for b in at.get("download_button")] == ["Download JSON"]
