from __future__ import annotations

import asyncio
import json
from io import BytesIO

from fastapi import UploadFile
import fastapi.dependencies.utils as dependency_utils

dependency_utils.ensure_multipart_is_installed = lambda: None  # type: ignore

from backend.app.ingest import parse


class _DummyAI:
    async def chat(self, system: str, user: str) -> str:  # pragma: no cover - exercised below
        assert "Base64 file" in user
        return json.dumps(
            {
                "contacts": {
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1 555-0100",
                    "location": "Remote",
                    "links": ["https://linkedin.com/in/johndoe"],
                },
                "experience": [
                    {
                        "company": "Acme",
                        "role": "Engineer",
                        "period": "2020-2022",
                        "responsibilities": ["Built APIs"],
                        "achievements": ["Reduced latency by 30%"],
                    }
                ],
                "education": [
                    {
                        "institution": "MIT",
                        "degree": "BS Computer Science",
                        "period": "2014-2018",
                        "details": ["Honors"],
                    }
                ],
                "skills": ["Python", "FastAPI"],
            }
        )


def test_parse_returns_structured_data(monkeypatch):
    monkeypatch.setattr("backend.app.ingest.get_ai", lambda: _DummyAI())

    upload = UploadFile(filename="resume.txt", file=BytesIO(b"John Doe\nEngineer"))

    response = asyncio.run(parse(upload))

    assert response.raw_text.startswith("John Doe")
    assert response.structured is not None
    assert response.structured.contacts is not None
    assert response.structured.contacts.full_name == "John Doe"
    assert response.structured.experience[0].company == "Acme"
    assert response.structured.skills == ["Python", "FastAPI"]
    assert response.ocr_error is None


def test_parse_reports_ocr_errors(monkeypatch):
    def raise_get_ai():
        raise RuntimeError("missing API key")

    monkeypatch.setattr("backend.app.ingest.get_ai", raise_get_ai)

    upload = UploadFile(filename="resume.txt", file=BytesIO(b"Jane Doe"))

    response = asyncio.run(parse(upload))

    assert response.raw_text.startswith("Jane Doe")
    assert response.structured is None
    assert response.ocr_error is not None
    assert "misconfiguration" in response.ocr_error
