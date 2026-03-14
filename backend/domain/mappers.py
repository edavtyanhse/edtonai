"""Mappers for converting between ORM models and domain dicts.

These functions extract the "get_parsed_data / set_parsed_data" business logic
that was previously embedded in ORM models, keeping ORM models as pure
table mappings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.models.resume import ResumeRaw
    from backend.models.vacancy import VacancyRaw


# ── Resume mapping ────────────────────────────────────────────────


def get_resume_parsed_data(resume: ResumeRaw) -> dict[str, Any]:
    """Assemble parsed resume data from individual ORM columns."""
    return {
        "personal_info": resume.personal_info,
        "summary": resume.summary,
        "skills": resume.skills or [],
        "work_experience": resume.work_experience or [],
        "education": resume.education or [],
        "certifications": resume.certifications or [],
        "languages": resume.languages or [],
        "raw_sections": resume.raw_sections or {},
    }


def set_resume_parsed_data(resume: ResumeRaw, data: dict[str, Any]) -> None:
    """Distribute a parsed-data dict into individual ORM columns."""
    resume.personal_info = data.get("personal_info")
    resume.summary = data.get("summary")
    resume.skills = data.get("skills", [])
    resume.work_experience = data.get("work_experience", [])
    resume.education = data.get("education", [])
    resume.certifications = data.get("certifications", [])
    resume.languages = data.get("languages", [])
    resume.raw_sections = data.get("raw_sections", {})


# ── Vacancy mapping ──────────────────────────────────────────────


def get_vacancy_parsed_data(vacancy: VacancyRaw) -> dict[str, Any]:
    """Assemble parsed vacancy data from individual ORM columns."""
    return {
        "job_title": vacancy.job_title,
        "company": vacancy.company,
        "employment_type": vacancy.employment_type,
        "location": vacancy.location,
        "required_skills": vacancy.required_skills or [],
        "preferred_skills": vacancy.preferred_skills or [],
        "experience_requirements": vacancy.experience_requirements,
        "responsibilities": vacancy.responsibilities or [],
        "ats_keywords": vacancy.ats_keywords or [],
    }


def set_vacancy_parsed_data(vacancy: VacancyRaw, data: dict[str, Any]) -> None:
    """Distribute a parsed-data dict into individual ORM columns."""
    vacancy.job_title = data.get("job_title")
    vacancy.company = data.get("company")
    vacancy.employment_type = data.get("employment_type")
    vacancy.location = data.get("location")
    vacancy.required_skills = data.get("required_skills", [])
    vacancy.preferred_skills = data.get("preferred_skills", [])
    vacancy.experience_requirements = data.get("experience_requirements")
    vacancy.responsibilities = data.get("responsibilities", [])
    vacancy.ats_keywords = data.get("ats_keywords", [])
