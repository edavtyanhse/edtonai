"""Shared Pydantic schemas used across FastAPI routes."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: List[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    company: str | None = None
    role: str | None = None
    period: str | None = None
    responsibilities: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    period: str | None = None
    details: List[str] = Field(default_factory=list)


class ParsedResumePayload(BaseModel):
    contacts: ContactInfo | None = None
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)


class ParseResumeResponse(BaseModel):
    raw_text: str
    structured: ParsedResumePayload | None = None
    ocr_error: str | None = None
