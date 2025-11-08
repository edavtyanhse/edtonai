"""Utilities for parsing uploaded resume files into structured UTF-8 text."""
from __future__ import annotations

import json
from io import BytesIO

from fastapi import APIRouter, HTTPException, UploadFile
from pdfminer.high_level import extract_text as pdf_extract_text
from pydantic import BaseModel, ConfigDict, Field
import chardet
import docx

from .prompts import PROMPT_SYSTEM_PARSE, PROMPT_USER_PARSE
from .providers import get_ai

router = APIRouter()


class ContactInfo(BaseModel):
    full_name: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    links: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    company: str | None = None
    position: str | None = None
    period: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    period: str | None = None
    details: list[str] = Field(default_factory=list)


class ResumeStructured(BaseModel):
    summary: str | None = None
    contact: ContactInfo = Field(default_factory=ContactInfo)
    experiences: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class ParseResumeOut(ResumeStructured):
    raw_text: str
    warnings: list[str] = Field(default_factory=list)


def _decode_bytes(data: bytes) -> str:
    """Decode arbitrary bytes into UTF-8, best-effort."""
    detection = chardet.detect(data)
    encoding = (detection.get("encoding") or "utf-8").lower()
    try:
        return data.decode(encoding, errors="ignore")
    except Exception:
        return data.decode("utf-8", errors="ignore")


def _coerce_json_block(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("AI ответ не похож на JSON")
    return text[start : end + 1]


async def _structure_resume(raw_text: str) -> tuple[ResumeStructured, list[str]]:
    warnings: list[str] = []
    if not raw_text.strip():
        warnings.append("Файл не содержит текста")
        return ResumeStructured(), warnings

    try:
        ai = get_ai()
        response = await ai.chat(
            system=PROMPT_SYSTEM_PARSE,
            user=PROMPT_USER_PARSE.format(resume=raw_text),
        )
        payload = json.loads(_coerce_json_block(response))
        structured = ResumeStructured.model_validate(payload)
        return structured, warnings
    except Exception as exc:  # pragma: no cover - AI может вернуть что угодно
        warnings.append(f"AI parse error: {exc}")
        return ResumeStructured(), warnings


@router.post("/api/parse", response_model=ParseResumeOut)
async def parse(file: UploadFile) -> ParseResumeOut:
    """Extract plain UTF-8 text from supported resume file formats and structure it."""
    filename = (file.filename or "").lower()
    raw = await file.read()

    try:
        if filename.endswith(".pdf"):
            text = pdf_extract_text(BytesIO(raw))
        elif filename.endswith(".docx"):
            document = docx.Document(BytesIO(raw))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        elif filename.endswith(".doc"):
            # .doc файлы часто распознаются как двоичные, попытаемся декодировать их как текст
            text = _decode_bytes(raw)
        elif filename.endswith(".txt") or filename.endswith(".md"):
            text = _decode_bytes(raw)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF/DOCX/TXT.")
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive, unexpected parsing errors
        raise HTTPException(status_code=422, detail=f"Parse error: {exc}") from exc

    structured, warnings = await _structure_resume(text)
    return ParseResumeOut(raw_text=text, warnings=warnings, **structured.model_dump())
