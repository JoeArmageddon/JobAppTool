"""
Unit tests for resume_tailor service.

Focuses on the resume integrity constraint — verifying the prompts contain
the required non-hallucination language.
"""

import json

import pytest

from services.resume_tailor import GAP_ANALYSIS_PROMPT, REWRITE_PROMPT


class TestResumeIntegrityConstraint:
    """Verify that the resume integrity constraint is present verbatim in prompts."""

    REQUIRED_PHRASES = [
        "Never invent",
        "never exaggerate",
        "never hallucinate",
        "Do NOT add skills not in the original",
        "ONLY facts present in the original resume",
    ]

    def test_rewrite_prompt_contains_integrity_phrases(self) -> None:
        """REWRITE_PROMPT must contain all required integrity constraint phrases."""
        for phrase in self.REQUIRED_PHRASES:
            assert phrase in REWRITE_PROMPT, (
                f"Resume integrity phrase missing from REWRITE_PROMPT: '{phrase}'\n"
                "This is a product failure, not a bug. Add the phrase verbatim."
            )

    def test_rewrite_prompt_includes_resume_placeholder(self) -> None:
        """REWRITE_PROMPT must include {resume} and {jd} format placeholders."""
        assert "{resume}" in REWRITE_PROMPT
        assert "{jd}" in REWRITE_PROMPT
        assert "{gap_analysis}" in REWRITE_PROMPT

    def test_gap_analysis_prompt_includes_placeholders(self) -> None:
        """GAP_ANALYSIS_PROMPT must include {resume} and {jd} placeholders."""
        assert "{resume}" in GAP_ANALYSIS_PROMPT
        assert "{jd}" in GAP_ANALYSIS_PROMPT

    def test_rewrite_prompt_does_not_allow_invention(self) -> None:
        """Verify the prompt explicitly prohibits adding credentials not in the resume."""
        prohibited_additions = [
            "certifications or degrees not explicitly stated",
            "Do NOT add",
        ]
        for phrase in prohibited_additions:
            assert phrase in REWRITE_PROMPT, (
                f"Expected prohibition phrase not found in REWRITE_PROMPT: '{phrase}'"
            )


class TestPromptFormatting:
    """Test that prompts format correctly with real data."""

    def test_gap_analysis_prompt_formats_without_error(self, sample_resume_json) -> None:
        prompt = GAP_ANALYSIS_PROMPT.format(
            resume=json.dumps(sample_resume_json, indent=2),
            jd="Looking for a senior Python developer with FastAPI experience.",
        )
        assert "Jane Smith" in prompt
        assert "FastAPI" in prompt

    def test_rewrite_prompt_formats_without_error(self, sample_resume_json) -> None:
        gap = {
            "exact_matches": ["Python"],
            "synonym_matches": [],
            "skill_gaps": ["Go"],
            "reorder_suggestions": [],
            "keyword_density_score": 70,
        }
        prompt = REWRITE_PROMPT.format(
            resume=json.dumps(sample_resume_json, indent=2),
            gap_analysis=json.dumps(gap, indent=2),
            jd="Looking for a senior Python developer.",
        )
        assert "Jane Smith" in prompt
        assert "Python" in prompt

    @pytest.fixture
    def sample_resume_json(self) -> dict:
        return {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "skills": ["Python", "FastAPI"],
            "experience": [],
            "education": [],
        }
