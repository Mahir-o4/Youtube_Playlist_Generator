"""Input schema for syllabus decomposition."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class StrictTextModel(BaseModel):
    """Strip surrounding whitespace from every string before validation."""

    @field_validator("*", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class SyllabusInput(StrictTextModel):
    subject: str = Field(min_length=1, max_length=200)
    level: str = Field(min_length=1, max_length=100)
    language: str = Field(min_length=1, max_length=100)
    syllabus: str = Field(min_length=20, description="Raw syllabus module text")
