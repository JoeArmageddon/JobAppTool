"""
Resume scorer — evaluates ATS-friendliness, impact, and completeness via Claude.
Returns numeric scores (0–100) and actionable suggestions.
"""

import json
import os
from typing import Any

import anthropic
from loguru import logger

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SCORE_PROMPT = """You are an expert resume reviewer and ATS specialist.

Evaluate the resume JSON below on three dimensions and return a JSON response only.

Scoring criteria:
1. ATS Score (0-100): keyword richness, standard section names (Experience, Education, Skills),
   absence of tables/graphics/headers/footers that confuse parsers, use of standard fonts implied
   by text quality, action verbs present.
2. Impact Score (0-100): percentage of bullet points that start with strong action verbs AND
   contain quantified results (numbers, percentages, dollar amounts). Pure responsibility bullets
   with no metrics score lower.
3. Completeness Score (0-100): presence of name, contact info, summary, skills, experience,
   education, and (bonus) projects/certifications.

Return ONLY this JSON structure (no markdown, no commentary):
{
  "ats_score": <number 0-100>,
  "impact_score": <number 0-100>,
  "completeness_score": <number 0-100>,
  "overall_score": <weighted average: ats*0.35 + impact*0.40 + completeness*0.25>,
  "suggestions": [
    {
      "category": "<ATS | Impact | Completeness>",
      "issue": "<specific problem found>",
      "fix": "<specific actionable fix>"
    }
  ]
}

Return 3–7 suggestions, ordered by impact. Be specific and concrete.

Resume JSON:
"""


async def score_resume(structured_json: dict[str, Any]) -> dict[str, Any]:
    """Score a parsed resume and return scores + suggestions."""
    try:
        message = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": SCORE_PROMPT + json.dumps(structured_json, indent=2),
                }
            ],
        )
        content = message.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
        result = json.loads(content)

        # Clamp scores to valid range
        for key in ("ats_score", "impact_score", "completeness_score", "overall_score"):
            result[key] = max(0.0, min(100.0, float(result.get(key, 0))))

        return result
    except anthropic.APIError as exc:
        logger.error(f"Claude API error during resume scoring: {exc}")
        raise RuntimeError("Resume scoring service temporarily unavailable") from exc
    except json.JSONDecodeError as exc:
        logger.error(f"Claude returned invalid JSON during scoring: {exc}")
        raise RuntimeError("Resume scorer returned malformed data") from exc
