"""Structured syllabus breakdown schemas."""

from __future__ import annotations

from pydantic import Field, model_validator

from schemas.input import StrictTextModel


class ChecklistItem(StrictTextModel):
    text: str = Field(min_length=3, description="One checkable skill or concept")


class LearningUnit(StrictTextModel):
    title: str = Field(min_length=3)
    objective: str = Field(min_length=3)
    checklist: list[ChecklistItem] = Field(min_length=1)
    search_query: str = Field(
        min_length=3,
        description="YouTube search query in the syllabus language",
    )


class Topic(StrictTextModel):
    title: str = Field(min_length=3)
    summary: str = Field(min_length=3)
    units: list[LearningUnit] = Field(min_length=1)


class SyllabusBreakdown(StrictTextModel):
    subject: str = Field(min_length=1)
    level: str = Field(min_length=1)
    topics: list[Topic] = Field(min_length=1)

    @model_validator(mode="after")
    def check_unique_titles(self) -> SyllabusBreakdown:
        topic_titles = [topic.title.casefold() for topic in self.topics]
        if len(topic_titles) != len(set(topic_titles)):
            raise ValueError("topic titles must be unique")
        for topic in self.topics:
            unit_titles = [unit.title.casefold() for unit in topic.units]
            if len(unit_titles) != len(set(unit_titles)):
                raise ValueError(
                    f"unit titles must be unique within topic {topic.title!r}"
                )
        return self
