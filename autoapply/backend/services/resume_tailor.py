"""
Resume tailoring engine.

⚠️ RESUME INTEGRITY — NON-NEGOTIABLE ⚠️
Claude must NEVER add skills, experience, credentials, or facts not present
in the original resume. Every prompt includes this constraint verbatim.
Violation is a product failure, not a bug.
"""

import json
import os
from typing import Any

import anthropic
from loguru import logger

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

GAP_ANALYSIS_PROMPT = """You are a resume optimization expert performing a gap analysis.

Given a candidate's resume and a target job description, identify:
1. Exact keyword matches (words appearing in both)
2. Synonym/concept matches (same idea, different wording)
3. Skills and requirements in the JD NOT present in the resume (gaps)
4. Sections or bullets that could be reordered to lead with most relevant content

Return ONLY this JSON (no markdown):
{
  "exact_matches": [],
  "synonym_matches": [{"resume_term": "", "jd_term": ""}],
  "skill_gaps": [],
  "reorder_suggestions": [],
  "keyword_density_score": <0-100>
}

Resume JSON:
{resume}

Job Description:
{jd}
"""

REWRITE_PROMPT = """You are a professional resume writer. Your task is to tailor a resume for a specific job.

CRITICAL CONSTRAINT — READ BEFORE WRITING:
You MUST use ONLY facts present in the original resume.
Never invent, never exaggerate, never hallucinate.
- Do NOT add skills not in the original
- Do NOT invent job titles, companies, dates, or responsibilities
- Do NOT add certifications or degrees not explicitly stated
- Do NOT exaggerate or embellish any achievement
- Do NOT infer experience and present it as fact

You MAY:
- Reorder sections/bullets to lead with the most relevant content for this role
- Reframe existing bullets using keywords and language from the JD
- Strengthen impact language where numbers ALREADY exist in the resume
- Incorporate exact JD keywords naturally into existing bullet points

Return the full tailored resume as JSON matching the EXACT same schema as the original resume.
Return ONLY valid JSON, no markdown.

Original resume JSON:
{resume}

Gap analysis:
{gap_analysis}

Target job description:
{jd}
"""


async def analyze_gap(resume_json: dict[str, Any], jd_text: str) -> dict[str, Any]:
    """Step 1: Identify gaps and match opportunities between resume and JD."""
    try:
        prompt = GAP_ANALYSIS_PROMPT.format(
            resume=json.dumps(resume_json, indent=2),
            jd=jd_text,
        )
        message = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
        return json.loads(content)
    except anthropic.APIError as exc:
        logger.error(f"Claude API error during gap analysis: {exc}")
        raise RuntimeError("Gap analysis service temporarily unavailable") from exc


async def rewrite_resume(
    resume_json: dict[str, Any],
    gap_analysis: dict[str, Any],
    jd_text: str,
) -> dict[str, Any]:
    """
    Step 2: Rewrite resume to be optimized for the target role.

    ⚠️ Resume integrity: only uses facts already in the resume.
    """
    try:
        prompt = REWRITE_PROMPT.format(
            resume=json.dumps(resume_json, indent=2),
            gap_analysis=json.dumps(gap_analysis, indent=2),
            jd=jd_text,
        )
        message = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
        return json.loads(content)
    except anthropic.APIError as exc:
        logger.error(f"Claude API error during resume rewrite: {exc}")
        raise RuntimeError("Resume tailoring service temporarily unavailable") from exc


async def tailor_resume(
    resume_json: dict[str, Any], jd_text: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Full tailoring pipeline: gap analysis → rewrite.
    Returns (tailored_resume_json, gap_analysis).
    """
    gap_analysis = await analyze_gap(resume_json, jd_text)
    tailored = await rewrite_resume(resume_json, gap_analysis, jd_text)
    return tailored, gap_analysis
