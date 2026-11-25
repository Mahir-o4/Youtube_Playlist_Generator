"""Streamlit result rendering, organized around units."""

from __future__ import annotations

import csv
import io
import json

import streamlit as st

from schemas import CoverageReport, PlaylistItem, SyllabusBreakdown

_COVERAGE_ICONS = {"covered": "✅", "partial": "◐", "missing": "❌"}


def _clean_timestamp(value: str | None) -> str:
    return value.strip("[]") if value else "start"


def _coverage_map(coverage: CoverageReport | None) -> dict[str, dict[str, tuple[str, str | None]]]:
    if not coverage:
        return {}
    result: dict[str, dict[str, tuple[str, str | None]]] = {}
    for entry in coverage.items:
        result.setdefault(entry.unit_key, {})[entry.item] = (
            entry.status,
            entry.evidence_timestamp,
        )
    return result


def render_breakdown(
    breakdown: SyllabusBreakdown,
    finalists: dict[str, list] | None = None,
    playlist: list[PlaylistItem] | None = None,
    coverage: CoverageReport | None = None,
) -> None:
    """Render topics with units, checklists, coverage, and video links inline."""
    unit_count = sum(len(topic.units) for topic in breakdown.topics)
    st.success(f"{len(breakdown.topics)} topics · {unit_count} searchable units")

    coverage_by_unit = _coverage_map(coverage)
    playlist_by_unit = {item.unit_key: item for item in (playlist or [])}
    finalists = finalists or {}

    for topic_index, topic in enumerate(breakdown.topics, start=1):
        with st.expander(f"{topic_index}. {topic.title}", expanded=topic_index == 1):
            st.caption(topic.summary)
            for unit_index, unit in enumerate(topic.units, start=1):
                unit_key = f"{topic_index}.{unit_index}"
                st.subheader(f"{unit_key} {unit.title}")
                st.caption(unit.objective)

                st.markdown("**Checklist**")
                for item in unit.checklist:
                    status, timestamp = coverage_by_unit.get(unit_key, {}).get(
                        item.text, (None, None)
                    )
                    if status:
                        prefix = _COVERAGE_ICONS.get(status, "•")
                        suffix = f" · `{_clean_timestamp(timestamp)}`" if timestamp else ""
                        st.markdown(f"{prefix} {item.text}{suffix}")
                    else:
                        st.markdown(f"— {item.text} · _no transcript evidence_")

                st.caption(f"YouTube search: {unit.search_query}")

                selected = playlist_by_unit.get(unit_key)
                if selected:
                    jump = _clean_timestamp(selected.start_timestamp)
                    st.markdown(
                        f"**Selected:** [{selected.video.title}]({selected.video.url}) "
                        f"· jump `{jump}` · score {selected.decision_score:.2f}"
                    )
                else:
                    candidates = finalists.get(unit_key, [])
                    if candidates:
                        st.caption("No video selected — no usable transcript evidence.")
                        with st.expander(f"Top {len(candidates)} candidates", expanded=False):
                            for video in candidates:
                                st.markdown(
                                    f"- [{video.title}]({video.url}) — "
                                    f"score {video.popularity_score:.2f}"
                                )
                    else:
                        st.caption("No candidates found for this unit.")


def render_downloads(
    breakdown: SyllabusBreakdown, playlist: list[PlaylistItem] | None = None
) -> None:
    json_col, csv_col = st.columns(2)
    with json_col:
        st.download_button(
            "Download JSON",
            data=json.dumps(breakdown.model_dump(), indent=2, ensure_ascii=False),
            file_name="syllabus-breakdown.json",
            mime="application/json",
        )
    if playlist:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["unit", "title", "url", "start", "score", "covered_checklist"])
        for item in playlist:
            writer.writerow(
                [
                    item.unit_key,
                    item.video.title,
                    item.video.url,
                    item.start_timestamp or "",
                    item.decision_score,
                    " | ".join(item.covered_checklist),
                ]
            )
        with csv_col:
            st.download_button(
                "Download playlist CSV",
                data=buffer.getvalue(),
                file_name="playlist.csv",
                mime="text/csv",
            )
