"""
PDF generator — converts tailored resume JSON to ATS-safe PDF via WeasyPrint.
Single-column layout. No tables, no graphics, standard fonts only.
"""

import json
import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger
from weasyprint import HTML

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", "/app/uploads"))


def _render_html(resume: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("resume.html")
    return template.render(r=resume)


def generate_pdf(resume_json: dict[str, Any], application_id: str) -> str:
    """
    Render resume JSON to ATS-safe PDF.
    Returns the file path of the generated PDF.
    """
    try:
        html_content = _render_html(resume_json)
        pdf_dir = UPLOADS_DIR / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / f"{application_id}.pdf"

        HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf(str(pdf_path))
        logger.info(f"[pdf_generator] Generated PDF: {pdf_path}")
        return str(pdf_path)
    except Exception as exc:
        logger.error(f"[pdf_generator] Error generating PDF for {application_id}: {exc}")
        raise RuntimeError("PDF generation failed") from exc
