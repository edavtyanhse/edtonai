from __future__ import annotations

from backend.app.models import DocumentKind
from backend.app.repositories import (
    create_analysis_record,
    get_analysis_detail,
    get_document,
    list_analyses,
    list_generations,
    persist_generation,
)


def test_analysis_and_generation_flow() -> None:
    user_id = "user-1"
    resume_text = "Python developer with API experience"
    vacancy_text = "Looking for a Python developer with FastAPI knowledge"

    analysis, resume, vacancy = create_analysis_record(
        user_id=user_id,
        resume_text=resume_text,
        vacancy_text=vacancy_text,
        role="Python Developer",
        match_score=75.0,
        matched_skills=["Python", "APIs"],
        missing_skills=["FastAPI"],
        tips="Focus on FastAPI projects",
        resume_skills=["Python", "APIs"],
        vacancy_keywords=["Python", "FastAPI"],
    )

    summaries = list_analyses(user_id)
    assert len(summaries) == 1
    assert summaries[0].id == analysis.id
    assert summaries[0].resume.title == "Python Developer"

    detail_analysis, detail_resume, detail_vacancy, documents = get_analysis_detail(
        user_id, analysis.id
    )
    assert detail_analysis.match_score == 75.0
    assert detail_resume.content == resume_text
    assert detail_vacancy.description == vacancy_text
    assert documents == []

    resume_doc, cover_doc, *_ = persist_generation(
        user_id=user_id,
        analysis_id=analysis.id,
        resume_text=resume_text,
        vacancy_text=vacancy_text,
        target_role="Python Developer",
        improved_resume="Improved resume",
        cover_letter="Cover letter body",
        ats_score=88.5,
        resume_skills=["Python", "APIs"],
        vacancy_keywords=["Python", "FastAPI"],
    )

    assert resume_doc.kind is DocumentKind.RESUME
    assert cover_doc.kind is DocumentKind.COVER_LETTER

    fetched_resume_doc = get_document(user_id, resume_doc.id)
    assert fetched_resume_doc.content == "Improved resume"

    bundles = list_generations(user_id)
    assert len(bundles) == 1
    bundle = bundles[0]
    assert bundle.analysis_id == analysis.id
    assert bundle.resume_document_id == resume_doc.id
    assert bundle.cover_letter_document_id == cover_doc.id
    assert bundle.ats_score == 88.5


def test_access_is_scoped_by_user() -> None:
    analysis, *_ = create_analysis_record(
        user_id="owner",
        resume_text="A",
        vacancy_text="B",
        role=None,
        match_score=0,
        matched_skills=[],
        missing_skills=[],
        tips="",
        resume_skills=[],
        vacancy_keywords=[],
    )

    try:
        get_analysis_detail("another", analysis.id)
    except ValueError as exc:
        assert "analysis not found" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("Expected ValueError for unauthorized access")
