"""Cover letter generator — 3-paragraph, max 280 words, professional."""

from typing import Any

from loguru import logger

from services.llm import complete

COVER_LETTER_PROMPT = """Write a cover letter for the following job application.

Requirements:
- Exactly 3 paragraphs
- Maximum 280 words total
- Professional and direct — not sycophantic, not generic
- Paragraph 1: Why this specific company and role. Use the company name. Reference one specific
  detail from the job description to show you read it carefully.
- Paragraph 2: Top 2–3 matching achievements from the candidate's resume mapped explicitly to
  the job requirements. Be specific with numbers if they exist.
- Paragraph 3: Forward-looking closer — how you'll contribute and a clear call to action.

Return ONLY the cover letter text. No subject line. No "Dear Hiring Manager". No signature.
Start directly with the first paragraph.

Candidate resume JSON:
{resume}

Job title: {job_title}
Company: {company}
Job description: {jd}
"""


async def generate_cover_letter(
    resume_json: dict[str, Any],
    job_title: str,
    company: str,
    jd_text: str,
) -> str:
    """Generate a tailored cover letter."""
    try:
        prompt = COVER_LETTER_PROMPT.format(
            resume=str(resume_json),
            job_title=job_title,
            company=company,
            jd=jd_text,
        )
        return await complete(prompt, max_tokens=1024)
    except RuntimeError as exc:
        logger.error(f"LLM error during cover letter generation: {exc}")
        raise RuntimeError("Cover letter service temporarily unavailable") from exc
