# backend/app/main.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .providers import get_ai
from .logic import extract_skills, compute_match, ats_score
from .prompts import (
    PROMPT_SYSTEM_ANALYSIS,
    PROMPT_USER_ANALYSIS,
    PROMPT_SYSTEM_RESUME,
    PROMPT_USER_RESUME,
    PROMPT_SYSTEM_CL,
    PROMPT_USER_CL,
)
from .db import db_health  # NEW: DB health-check
from .ingest import router as ingest_router

app = FastAPI(title="EdTon.ai API")

# ⚠️ На проде сузить origins до домена фронта (*.lovable.app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)

# ── Pydantic-модели ───────────────────────────────────────────────────────────
class AnalyzeIn(BaseModel):
    resume_text: str
    vacancy_text: str
    role: str | None = None


class AnalyzeOut(BaseModel):
    analysis_id: str
    resume_id: str
    vacancy_id: str
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    tips: str
    role: str | None = None
    created_at: datetime


class GenerateIn(BaseModel):
    analysis_id: str | None = None
    resume_text: str | None = None
    vacancy_text: str | None = None
    target_role: str | None = None

    @model_validator(mode="after")
    def validate_sources(self) -> "GenerateIn":
        if not self.analysis_id:
            if not self.resume_text or not self.vacancy_text:
                raise ValueError(
                    "analysis_id or both resume_text and vacancy_text must be provided"
                )
        return self


class GenerateOut(BaseModel):
    analysis_id: str
    resume_id: str
    vacancy_id: str
    resume_document_id: str
    cover_letter_document_id: str
    improved_resume: str
    cover_letter: str
    ats_score: float


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None = None
    content: str
    skills: list[str]
    created_at: datetime


class VacancyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str | None = None
    description: str
    keywords: list[str]
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    analysis_id: str
    kind: str
    content: str
    ats_score: float | None = None
    created_at: datetime


class AnalysisRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_id: str
    vacancy_id: str
    role: str | None = None
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    tips: str | None = None
    created_at: datetime


class AnalysisDetailOut(BaseModel):
    analysis: AnalysisRecordOut
    resume: ResumeOut
    vacancy: VacancyOut
    documents: list[DocumentOut]


class AnalysisSummaryOut(BaseModel):
    id: str
    resume_id: str
    vacancy_id: str
    role: str | None
    match_score: float
    created_at: datetime
    resume_title: str | None = None
    vacancy_title: str | None = None


class GenerationSummaryOut(BaseModel):
    analysis_id: str
    resume_document_id: str | None = None
    cover_letter_document_id: str | None = None
    ats_score: float | None = None
    created_at: datetime


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/db/health")
async def db_healthcheck():
    """Проверка доступности Postgres (SELECT 1)."""
    try:
        ok = db_health()
        return {"db_ok": bool(ok)}
    except Exception as e:  # pragma: no cover - defensive
        return {"db_ok": False, "error": str(e)}


@app.post("/api/analyze", response_model=AnalyzeOut)
async def analyze(payload: AnalyzeIn, user_id: str = Depends(get_current_user_id)):
    rs = extract_skills(payload.resume_text)
    vc = extract_skills(payload.vacancy_text)
    matched, missing, score = compute_match(rs, vc)

    try:
        raw_tips = await get_ai().chat(
            system=PROMPT_SYSTEM_ANALYSIS,
            user=PROMPT_USER_ANALYSIS.format(
                resume=payload.resume_text,
                vacancy=payload.vacancy_text,
                role=payload.role or "кандидат",
            ),
        )
        tips = raw_tips.strip()
    except Exception as e:
        tips = f"AI error: {e}"

    analysis, resume, vacancy = create_analysis_record(
        user_id=user_id,
        resume_text=payload.resume_text,
        vacancy_text=payload.vacancy_text,
        role=payload.role,
        match_score=score,
        matched_skills=matched,
        missing_skills=missing,
        tips=tips,
        resume_skills=rs,
        vacancy_keywords=vc,
    )

    return AnalyzeOut(
        analysis_id=analysis.id,
        resume_id=resume.id,
        vacancy_id=vacancy.id,
        match_score=score,
        matched_skills=list(matched),
        missing_skills=list(missing),
        tips=tips,
        role=analysis.role,
        created_at=analysis.created_at,
    )


@app.post("/api/generate", response_model=GenerateOut)
async def generate(payload: GenerateIn, user_id: str = Depends(get_current_user_id)):
    analysis_record = None
    resume_record = None
    vacancy_record = None

    resume_text = payload.resume_text
    vacancy_text = payload.vacancy_text

    if payload.analysis_id:
        try:
            analysis_record, resume_record, vacancy_record, _ = get_analysis_detail(
                user_id, payload.analysis_id
            )
        except ValueError as exc:  # pragma: no cover - defensive branch
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        resume_text = resume_record.content
        vacancy_text = vacancy_record.description
    if resume_text is None or vacancy_text is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="resume_text and vacancy_text are required",
        )

    resume_keywords = extract_skills(resume_text)
    vacancy_keywords = extract_skills(vacancy_text)

    if analysis_record is None:
        matched, missing, score_for_analysis = compute_match(
            resume_keywords, vacancy_keywords
        )
        analysis_record, resume_record, vacancy_record = create_analysis_record(
            user_id=user_id,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
            role=payload.target_role,
            match_score=score_for_analysis,
            matched_skills=matched,
            missing_skills=missing,
            tips="",
            resume_skills=resume_keywords,
            vacancy_keywords=vacancy_keywords,
        )

    ai = get_ai()

    try:
        resume_raw = await ai.chat(
            system=PROMPT_SYSTEM_RESUME,
            user=PROMPT_USER_RESUME.format(
                resume=resume_text,
                vacancy=vacancy_text,
                role=payload.target_role or analysis_record.role or "кандидат",
            ),
        )
        improved_resume = resume_raw.strip()
    except Exception as e:
        improved_resume = f"[AI error while generating resume]: {e}"

    try:
        resume_for_cover = (
            improved_resume
            if not improved_resume.startswith("[AI error")
            else payload.resume_text
        )
        cover_raw = await ai.chat(
            system=PROMPT_SYSTEM_CL,
            user=PROMPT_USER_CL.format(
                resume=resume_for_cover,
                vacancy=payload.vacancy_text,
                role=payload.target_role or "кандидат",
            ),
        )
        cover_letter = cover_raw.strip()
    except Exception as e:
        cover_letter = f"[AI error while generating cover letter]: {e}"

    score_source = (
        improved_resume if not improved_resume.startswith("[AI error") else payload.resume_text
    )
    score = ats_score(score_source, payload.vacancy_text)

    return GenerateOut(
        analysis_id=analysis_record.id,
        resume_id=resume_record.id,
        vacancy_id=vacancy_record.id,
        resume_document_id=resume_doc.id,
        cover_letter_document_id=cover_doc.id,
        improved_resume=improved_resume,
        cover_letter=cover_letter,
        ats_score=score,
    )
