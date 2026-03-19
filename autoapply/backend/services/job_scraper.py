"""
Job scraper — integrates jobspy for multi-source job discovery,
then parses JDs via Claude and scores match against resume.
"""

import json
import os
import uuid
from typing import Any

import anthropic
import pandas as pd
from jobspy import scrape_jobs
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

JD_PARSE_PROMPT = """Parse this job description into structured JSON. Return ONLY valid JSON, no markdown:

{
  "required_skills": [],
  "preferred_skills": [],
  "responsibilities": [],
  "qualifications": [],
  "experience_years_min": null,
  "seniority": "",
  "remote_type": "",
  "key_technologies": []
}

Job description:
"""

MATCH_PROMPT = """You are a job-resume matcher. Given a resume and job description, return a match score and reasons.

Return ONLY this JSON:
{
  "match_score": <number 0-100>,
  "matching_skills": [],
  "missing_skills": [],
  "strengths": [],
  "concerns": [],
  "recommendation": "<apply | consider | skip>"
}

Resume JSON:
{resume}

Job description JSON:
{job}
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def parse_jd(description: str) -> dict[str, Any]:
    """Parse a job description into structured JSON via Claude."""
    try:
        message = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": JD_PARSE_PROMPT + description}],
        )
        content = message.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
        return json.loads(content)
    except anthropic.APIError as exc:
        logger.error(f"Claude API error parsing JD: {exc}")
        raise


async def score_job_match(resume_json: dict, jd_parsed: dict) -> dict[str, Any]:
    """Score how well a resume matches a job description."""
    try:
        prompt = MATCH_PROMPT.format(
            resume=json.dumps(resume_json, indent=2),
            job=json.dumps(jd_parsed, indent=2),
        )
        message = _client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content.rsplit("```", 1)[0]
        result = json.loads(content)
        result["match_score"] = max(0.0, min(100.0, float(result.get("match_score", 0))))
        return result
    except anthropic.APIError as exc:
        logger.error(f"Claude API error scoring job match: {exc}")
        raise


def scrape_jobs_for_profile(
    target_titles: list[str],
    locations: list[str],
    job_sources: list[str],
    results_per_search: int = 25,
) -> list[dict[str, Any]]:
    """
    Scrape jobs from multiple sources using jobspy.
    Returns a list of raw job dicts.
    """
    # Map our source names to jobspy names
    source_map = {
        "linkedin": "linkedin",
        "indeed": "indeed",
        "glassdoor": "glassdoor",
        "zip_recruiter": "zip_recruiter",
        "wellfound": "linkedin",  # jobspy doesn't have Wellfound directly
        "naukri": "indeed",       # fallback
    }
    valid_sources = list({
        source_map.get(s, s) for s in job_sources
        if source_map.get(s, s) in ("linkedin", "indeed", "glassdoor", "zip_recruiter")
    })
    if not valid_sources:
        valid_sources = ["linkedin", "indeed"]

    all_jobs: list[dict] = []
    location = locations[0] if locations else "United States"

    for title in target_titles[:3]:  # Limit to top 3 titles per run
        try:
            logger.info(f"Scraping '{title}' in '{location}' from {valid_sources}")
            df: pd.DataFrame = scrape_jobs(
                site_name=valid_sources,
                search_term=title,
                location=location,
                results_wanted=results_per_search,
                hours_old=24,
            )
            for _, row in df.iterrows():
                job: dict = row.to_dict()
                # Normalize the job dict
                job["search_title"] = title
                job["source_job_id"] = str(job.get("id", uuid.uuid4()))
                all_jobs.append(job)
        except Exception as exc:
            logger.error(f"jobspy error for '{title}': {exc}")

    # Deduplicate by source_job_id
    seen: set = set()
    unique: list[dict] = []
    for job in all_jobs:
        jid = str(job.get("source_job_id", ""))
        if jid and jid not in seen:
            seen.add(jid)
            unique.append(job)

    logger.info(f"Scraped {len(unique)} unique jobs")
    return unique
