"""Utilities for parsing uploaded resume files into UTF-8 text."""
from __future__ import annotations

import base64
import json
from io import BytesIO

from fastapi import APIRouter, HTTPException, UploadFile
from pdfminer.high_level import extract_text as pdf_extract_text
from pydantic import ValidationError
import chardet
import docx

from .providers import get_ai
from .schemas import ParseResumeResponse, ParsedResumePayload

router = APIRouter()


SYSTEM_PROMPT = (
    "You are a precise resume parser. "
    "Return only valid JSON that matches the provided schema, without extra text."
)

USER_PROMPT_TEMPLATE = """
You receive a resume file encoded as base64. Extract the content and reply with JSON only.
Schema:
{{
  "contacts": {{
    "full_name": string|null,
    "email": string|null,
    "phone": string|null,
    "location": string|null,
    "links": [string]
  }},
  "experience": [{{
    "company": string|null,
    "role": string|null,
    "period": string|null,
    "responsibilities": [string],
    "achievements": [string]
  }}],
  "education": [{{
    "institution": string|null,
    "degree": string|null,
    "period": string|null,
    "details": [string]
  }}],
  "skills": [string]
}}
If a field is unknown use null or an empty array. Keep wording from the resume.
Base64 file:
{encoded}
"""


def _decode_bytes(data: bytes) -> str:
    """Decode arbitrary bytes into UTF-8, best-effort."""
    detection = chardet.detect(data)
    encoding = (detection.get("encoding") or "utf-8").lower()
    try:
        return data.decode(encoding, errors="ignore")
    except Exception:
        return data.decode("utf-8", errors="ignore")


def _extract_raw_text(filename: str, raw: bytes) -> str:
    try:
        if filename.endswith(".pdf"):
            return pdf_extract_text(BytesIO(raw))
        if filename.endswith(".docx"):
            document = docx.Document(BytesIO(raw))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        if filename.endswith(".txt") or filename.endswith(".md"):
            return _decode_bytes(raw)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive, unexpected parsing errors
        raise HTTPException(status_code=422, detail=f"Parse error: {exc}") from exc

    raise HTTPException(
        status_code=400,
        detail="Unsupported file type. Use PDF/DOCX/TXT.",
    )


async def _structured_parse(raw: bytes) -> tuple[ParsedResumePayload | None, str | None]:
    """Send raw bytes to DeepSeek and parse structured resume data."""

    encoded = base64.b64encode(raw).decode("ascii")
    try:
        ai = get_ai()
    except RuntimeError as exc:
        return None, f"OCR provider misconfiguration: {exc}"

    try:
        response = await ai.chat(
            system=SYSTEM_PROMPT,
            user=USER_PROMPT_TEMPLATE.format(encoded=encoded),
        )
    except Exception as exc:  # pragma: no cover - network/runtime errors
        return None, f"OCR request failed: {exc}"

    try:
        payload = json.loads(response)
    except json.JSONDecodeError as exc:
        return None, f"OCR response was not valid JSON: {exc}"

    try:
        return ParsedResumePayload.model_validate(payload), None
    except ValidationError as exc:
        return None, f"OCR response did not match schema: {exc}"


@router.post("/api/parse", response_model=ParseResumeResponse)
async def parse(file: UploadFile) -> ParseResumeResponse:
    """Extract plain UTF-8 text and structured resume data."""
    filename = (file.filename or "").lower()
    raw = await file.read()

    text = _extract_raw_text(filename, raw)

    structured, ocr_error = await _structured_parse(raw)

    return ParseResumeResponse(raw_text=text, structured=structured, ocr_error=ocr_error)
