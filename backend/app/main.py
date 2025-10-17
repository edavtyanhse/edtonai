# backend/app/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

app = FastAPI(title="EdTon.ai API")

# ⚠️ На проде сузить origins до домена фронта (*.lovable.app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: replace with ["https://<your>.lovable.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic-модели ───────────────────────────────────────────────────────────
class AnalyzeIn(BaseModel):
    resume_text: str
    vacancy_text: str
    role: str | None = None


class AnalyzeOut(BaseModel):
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    tips: str


class GenerateIn(BaseModel):
    resume_text: str
    vacancy_text: str
    target_role: str | None = None


class GenerateOut(BaseModel):
    improved_resume: str
    cover_letter: str
    ats_score: float


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
    except Exception as e:
        # Не роняем API — возвращаем ошибку текстом
        return {"db_ok": False, "error": str(e)}


@app.post("/api/analyze", response_model=AnalyzeOut)
async def analyze(payload: AnalyzeIn):
    # Базовый локальный анализ (эвристики)
    rs = extract_skills(payload.resume_text)
    vc = extract_skills(payload.vacancy_text)
    matched, missing, score = compute_match(rs, vc)

    # Советы от AI; если провайдер упал — вернём текст ошибки
    try:
        tips = await get_ai().chat(
            system=PROMPT_SYSTEM_ANALYSIS,
            user=PROMPT_USER_ANALYSIS.format(
                resume=payload.resume_text,
                vacancy=payload.vacancy_text,
                role=payload.role or "кандидат",
            ),
        )
        tips = tips.strip()
    except Exception as e:
        tips = f"AI error: {e}"

    return AnalyzeOut(
        match_score=score,
        matched_skills=matched,
        missing_skills=missing,
        tips=tips,
    )


@app.post("/api/generate", response_model=GenerateOut)
async def generate(payload: GenerateIn):
    ai = get_ai()

    try:
        improved_resume = await ai.chat(
            system=PROMPT_SYSTEM_RESUME,
            user=PROMPT_USER_RESUME.format(
                resume=payload.resume_text,
                vacancy=payload.vacancy_text,
                role=payload.target_role or "кандидат",
            ),
        ).strip()
    except Exception as e:
        improved_resume = f"[AI error while generating resume]: {e}"

    try:
        cover_letter = await ai.chat(
            system=PROMPT_SYSTEM_CL,
            user=PROMPT_USER_CL.format(
                resume=improved_resume,
                vacancy=payload.vacancy_text,
                role=payload.target_role or "кандидат",
            ),
        ).strip()
    except Exception as e:
        cover_letter = f"[AI error while generating cover letter]: {e}"

    score = ats_score(improved_resume, payload.vacancy_text)

    return GenerateOut(
        improved_resume=improved_resume,
        cover_letter=cover_letter,
        ats_score=score,
    )
