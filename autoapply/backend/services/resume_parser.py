"""
Resume parser — accepts PDF or DOCX, extracts text, sends to Claude for
structured JSON extraction.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import anthropic
import fitz  # PyMuPDF
from docx import Document
from loguru import logger

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

PARSE_PROMPT = """You are a resume parser. Extract all information from the resume text below into this exact JSON schema:

{
  "name": "",
  "email": "",
  "phone": "",
  "location": "",
  "linkedin": "",
  "github": "",
  "summary": "",
  "skills": [],
  "experience": [
    {
      "company": "",
      "title": "",
      "start_date": "",
      "end_date": "",
      "current": false,
      "responsibilities": [],
      "achievements": []
    }
  ],
  "education": [
    {
      "institution": "",
      "degree": "",
      "field": "",
      "start_date": "",
      "end_date": "",
      "gpa": ""
    }
  ],
  "certifications": [],
  "languages": [],
  "projects": [
    {
      "name": "",
      "description": "",
      "technologies": [],
      "url": ""
    }
  ]
}

Rules:
- Return ONLY valid JSON. No commentary. No markdown fences. No explanation.
- If a field is not present, use null for strings and [] for arrays.
- For current positions, set end_date to null and current to true.
- Preserve all factual information exactly as written — do not infer, embellish, or add anything.

Resume text:
"""


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        pages = [page.get_text() for page in doc]
    return "\n\n".join(pages).strip()


def _extract_text_from_docx(file_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        doc = Document(tmp_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def extract_text(file_bytes: bytes, content_type: str) -> str:
    """Extract raw text from PDF or DOCX bytes."""
    if "pdf" in content_type.lower():
        return _extract_text_from_pdf(file_bytes)
    elif "docx" in content_type.lower() or "word" in content_type.lower():
        return _extract_text_from_docx(file_bytes)
    raise ValueError(f"Unsupported file type: {content_type}")


async def parse_resume(raw_text: str) -> dict[str, Any]:
    """Send raw resume text to Claude and return structured JSON."""
    try:
        message = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": PARSE_PROMPT + raw_text,
                }
            ],
        )
        content = message.content[0].text.strip()
        # Strip markdown fences if Claude adds them despite instructions
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
        return json.loads(content)
    except anthropic.APIError as exc:
        logger.error(f"Claude API error during resume parsing: {exc}")
        raise RuntimeError("Resume parsing service temporarily unavailable") from exc
    except json.JSONDecodeError as exc:
        logger.error(f"Claude returned invalid JSON during resume parsing: {exc}")
        raise RuntimeError("Resume parser returned malformed data") from exc
