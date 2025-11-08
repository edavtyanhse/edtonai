from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .db import get_engine
from .models import Analysis, Document, DocumentKind, Resume, Vacancy


@dataclass
class GenerationBundle:
    analysis_id: str
    resume_document_id: Optional[str]
    cover_letter_document_id: Optional[str]
    ats_score: Optional[float]
    created_at: datetime


@contextmanager
def session_scope(engine: Optional[Engine] = None):
    """Provide a transactional scope around a series of operations."""

    eng = engine or get_engine()
    session = Session(eng, future=True)
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - defensive rollback
        session.rollback()
        raise
    finally:
        session.close()


def _detach(session: Session, *instances):
    for instance in instances:
        if instance is None:
            continue
        session.flush()
        session.refresh(instance)
        session.expunge(instance)
    return instances if len(instances) > 1 else instances[0]


def _ensure_resume(
    session: Session,
    *,
    user_id: str,
    content: str,
    title: Optional[str] = None,
    skills: Optional[Iterable[str]] = None,
) -> Resume:
    stmt = select(Resume).where(
        Resume.user_id == user_id,
        Resume.content == content,
    )
    resume = session.execute(stmt).scalar_one_or_none()
    if resume is None:
        resume = Resume(
            user_id=user_id,
            content=content,
            title=title,
            skills=list(skills or []),
        )
        session.add(resume)
    else:
        resume.title = title or resume.title
        if skills is not None:
            resume.skills = list(skills)
    return resume


def _ensure_vacancy(
    session: Session,
    *,
    user_id: str,
    description: str,
    title: Optional[str] = None,
    source_url: Optional[str] = None,
    keywords: Optional[Iterable[str]] = None,
) -> Vacancy:
    stmt = select(Vacancy).where(
        Vacancy.user_id == user_id,
        Vacancy.description == description,
    )
    vacancy = session.execute(stmt).scalar_one_or_none()
    if vacancy is None:
        vacancy = Vacancy(
            user_id=user_id,
            description=description,
            title=title,
            source_url=source_url,
            keywords=list(keywords or []),
        )
        session.add(vacancy)
    else:
        vacancy.title = title or vacancy.title
        vacancy.source_url = source_url or vacancy.source_url
        if keywords is not None:
            vacancy.keywords = list(keywords)
    return vacancy


def create_analysis_record(
    *,
    user_id: str,
    resume_text: str,
    vacancy_text: str,
    role: Optional[str],
    match_score: float,
    matched_skills: Iterable[str],
    missing_skills: Iterable[str],
    tips: str,
    resume_skills: Iterable[str],
    vacancy_keywords: Iterable[str],
) -> tuple[Analysis, Resume, Vacancy]:
    with session_scope() as session:
        resume = _ensure_resume(
            session,
            user_id=user_id,
            content=resume_text,
            title=role,
            skills=resume_skills,
        )
        vacancy = _ensure_vacancy(
            session,
            user_id=user_id,
            description=vacancy_text,
            title=role,
            keywords=vacancy_keywords,
        )
        analysis = Analysis(
            user_id=user_id,
            resume=resume,
            vacancy=vacancy,
            role=role,
            match_score=match_score,
            matched_skills=list(matched_skills),
            missing_skills=list(missing_skills),
            tips=tips,
        )
        session.add(analysis)
        resume, vacancy, analysis = _detach(session, resume, vacancy, analysis)
        return analysis, resume, vacancy


def persist_generation(
    *,
    user_id: str,
    analysis_id: str,
    resume_text: str,
    vacancy_text: str,
    target_role: Optional[str],
    improved_resume: str,
    cover_letter: str,
    ats_score: float,
    resume_skills: Iterable[str],
    vacancy_keywords: Iterable[str],
) -> tuple[Document, Document, Analysis, Resume, Vacancy]:
    with session_scope() as session:
        analysis = session.get(Analysis, analysis_id)
        if analysis is None or analysis.user_id != user_id:
            raise ValueError("analysis not found for user")

        resume = _ensure_resume(
            session,
            user_id=user_id,
            content=resume_text,
            title=target_role or analysis.role,
            skills=resume_skills,
        )
        vacancy = _ensure_vacancy(
            session,
            user_id=user_id,
            description=vacancy_text,
            title=target_role or analysis.role,
            keywords=vacancy_keywords,
        )
        analysis.resume = resume
        analysis.vacancy = vacancy
        if target_role and not analysis.role:
            analysis.role = target_role

        resume_doc = Document(
            user_id=user_id,
            analysis=analysis,
            kind=DocumentKind.RESUME,
            content=improved_resume,
            ats_score=ats_score,
        )
        cover_doc = Document(
            user_id=user_id,
            analysis=analysis,
            kind=DocumentKind.COVER_LETTER,
            content=cover_letter,
            ats_score=ats_score,
        )
        session.add_all([resume_doc, cover_doc])

        resume_doc, cover_doc, analysis, resume, vacancy = _detach(
            session, resume_doc, cover_doc, analysis, resume, vacancy
        )
        return resume_doc, cover_doc, analysis, resume, vacancy


def list_analyses(user_id: str) -> List[Analysis]:
    with session_scope() as session:
        stmt = (
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
        )
        analyses = session.execute(stmt).scalars().all()
        results: List[Analysis] = []
        for analysis in analyses:
            # ensure relationships are loaded before the session closes
            resume = analysis.resume
            vacancy = analysis.vacancy
            if resume is not None:
                session.expunge(resume)
            if vacancy is not None:
                session.expunge(vacancy)
            session.expunge(analysis)
            results.append(analysis)
        return results


def get_analysis_detail(user_id: str, analysis_id: str) -> tuple[Analysis, Resume, Vacancy, List[Document]]:
    with session_scope() as session:
        analysis = session.get(Analysis, analysis_id)
        if analysis is None or analysis.user_id != user_id:
            raise ValueError("analysis not found for user")
        resume = analysis.resume
        vacancy = analysis.vacancy
        documents = list(analysis.documents)
        session.expunge(analysis)
        session.expunge(resume)
        session.expunge(vacancy)
        for doc in documents:
            session.expunge(doc)
        return analysis, resume, vacancy, documents


def get_document(user_id: str, document_id: str) -> Document:
    with session_scope() as session:
        document = session.get(Document, document_id)
        if document is None or document.user_id != user_id:
            raise ValueError("document not found for user")
        session.expunge(document)
        return document


def list_generations(user_id: str) -> List[GenerationBundle]:
    with session_scope() as session:
        stmt = select(Document).where(Document.user_id == user_id)
        documents = session.execute(stmt).scalars().all()
        bundles: Dict[str, Dict[str, Optional[object]]] = defaultdict(
            lambda: {
                "analysis_id": None,
                "resume_document_id": None,
                "cover_letter_document_id": None,
                "ats_score": None,
                "created_at": None,
            }
        )
        for document in documents:
            session.expunge(document)
            analysis_id = document.analysis_id
            bundle = bundles[analysis_id]
            bundle["analysis_id"] = analysis_id
            bundle["created_at"] = document.created_at
            bundle["ats_score"] = document.ats_score
            if document.kind == DocumentKind.RESUME:
                bundle["resume_document_id"] = document.id
            elif document.kind == DocumentKind.COVER_LETTER:
                bundle["cover_letter_document_id"] = document.id
        ordered_dicts = sorted(
            bundles.values(), key=lambda item: item["created_at"], reverse=True
        )
        return [
            GenerationBundle(
                analysis_id=entry["analysis_id"],
                resume_document_id=entry["resume_document_id"],
                cover_letter_document_id=entry["cover_letter_document_id"],
                ats_score=entry["ats_score"],
                created_at=entry["created_at"],
            )
            for entry in ordered_dicts
            if entry["analysis_id"] is not None
        ]
