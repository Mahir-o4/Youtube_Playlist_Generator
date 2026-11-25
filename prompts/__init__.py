"""Prompt templates loaded from plain text files."""

from __future__ import annotations

from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from schemas import SyllabusInput

_PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    """Load prompts/<name>.txt, stripping outer whitespace."""
    return (_PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()


def build_decomposition_messages(data: SyllabusInput) -> list[BaseMessage]:
    """Build chat messages for one syllabus decomposition request."""
    human = f"""\
Subject: {data.subject}
Academic level: {data.level}
Preferred language: {data.language}

Syllabus module:
---
{data.syllabus}
---

Decompose this module into topics, learning units, checklists, and YouTube search queries.
"""
    return [
        SystemMessage(content=load_prompt("decomposition")),
        HumanMessage(content=human),
    ]
