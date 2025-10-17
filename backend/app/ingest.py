"""Utilities for parsing uploaded resume files into UTF-8 text."""
from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pdfminer.high_level import extract_text as pdf_extract_text
import chardet
import docx

router = APIRouter()


def _decode_bytes(data: bytes) -> str:
    """Decode arbitrary bytes into UTF-8, best-effort."""
    detection = chardet.detect(data)
    encoding = (detection.get("encoding") or "utf-8").lower()
    try:
        return data.decode(encoding, errors="ignore")
    except Exception:
        return data.decode("utf-8", errors="ignore")


@router.post("/api/parse", response_class=PlainTextResponse)
async def parse(file: UploadFile) -> str:
    """Extract plain UTF-8 text from supported resume file formats."""
    filename = (file.filename or "").lower()
    raw = await file.read()

    try:
        if filename.endswith(".pdf"):
            text = pdf_extract_text(BytesIO(raw))
        elif filename.endswith(".docx"):
            document = docx.Document(BytesIO(raw))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        elif filename.endswith(".txt") or filename.endswith(".md"):
            text = _decode_bytes(raw)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF/DOCX/TXT.")
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive, unexpected parsing errors
        raise HTTPException(status_code=422, detail=f"Parse error: {exc}") from exc

    return text
