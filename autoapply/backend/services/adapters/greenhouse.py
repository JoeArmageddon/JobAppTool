"""
Greenhouse ATS adapter.
Handles jobs.greenhouse.io application forms.
"""

import json
import os
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from loguru import logger
from playwright.async_api import Page

from models.orm import Application

ApplyOutcome = Literal["success", "failed", "requires_human"]

SCREENSHOTS_DIR = Path(os.environ.get("UPLOADS_DIR", "/app/uploads")) / "screenshots"


async def _slow_type(page: Page, selector: str, text: str) -> None:
    """Type with human-like random delays between keystrokes."""
    await page.click(selector)
    for char in text:
        await page.type(selector, char, delay=random.randint(40, 120))


async def apply_greenhouse(page: Page, application: Application) -> ApplyOutcome:
    """
    Apply to a Greenhouse job posting.
    Returns success | failed | requires_human.
    """
    job = application.job
    if not job:
        return "requires_human"

    url = job.source_url
    resume_data = {}
    if application.tailored_resume_text:
        try:
            resume_data = json.loads(application.tailored_resume_text)
        except json.JSONDecodeError:
            resume_data = {}

    try:
        logger.info(f"[greenhouse] Navigating to {url}")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(random.randint(1000, 2000))

        # Check if this is actually a Greenhouse form
        is_greenhouse = await page.query_selector("#application-form, .application-form, [data-qa='submit-app']")
        if not is_greenhouse:
            logger.info(f"[greenhouse] No Greenhouse form found at {url}")
            return "requires_human"

        # Fill first name
        first_name = (resume_data.get("name", "") or "").split()[0] if resume_data.get("name") else ""
        last_name = " ".join((resume_data.get("name", "") or "").split()[1:]) if resume_data.get("name") else ""

        if await page.query_selector("#first_name"):
            await _slow_type(page, "#first_name", first_name)
            await page.wait_for_timeout(random.randint(500, 1000))

        if await page.query_selector("#last_name"):
            await _slow_type(page, "#last_name", last_name)
            await page.wait_for_timeout(random.randint(500, 1000))

        if await page.query_selector("#email"):
            email = resume_data.get("email", "")
            await _slow_type(page, "#email", email)
            await page.wait_for_timeout(random.randint(500, 1000))

        if await page.query_selector("#phone"):
            phone = resume_data.get("phone", "")
            await _slow_type(page, "#phone", phone)
            await page.wait_for_timeout(random.randint(500, 1000))

        # Cover letter
        cover_letter_field = await page.query_selector("textarea[name='cover_letter'], #cover_letter")
        if cover_letter_field and application.cover_letter_text:
            await cover_letter_field.click()
            await page.wait_for_timeout(random.randint(300, 700))
            await cover_letter_field.fill(application.cover_letter_text)

        await page.wait_for_timeout(random.randint(1000, 2500))

        # Screenshot before submit
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / f"{application.id}_greenhouse_preflight.png"
        await page.screenshot(path=str(screenshot_path))

        # If we got this far but need PDF upload, defer to human
        resume_upload = await page.query_selector("input[type='file']")
        if resume_upload and not application.tailored_resume_pdf_url:
            logger.info(f"[greenhouse] PDF upload required but no PDF generated, requires human")
            return "requires_human"

        # Submit
        submit_btn = await page.query_selector("[data-qa='submit-app'], input[type='submit']")
        if not submit_btn:
            logger.warning(f"[greenhouse] No submit button found")
            return "requires_human"

        await submit_btn.click()
        await page.wait_for_timeout(random.randint(2000, 4000))

        # Confirm success
        success_indicator = await page.query_selector(
            ".confirmation, .success, [data-qa='application-confirmation']"
        )
        if success_indicator:
            # Screenshot confirmation
            confirm_path = SCREENSHOTS_DIR / f"{application.id}_greenhouse_confirm.png"
            await page.screenshot(path=str(confirm_path))
            application.screenshot_url = str(confirm_path)
            logger.info(f"[greenhouse] Successfully applied for application {application.id}")
            return "success"

        logger.warning(f"[greenhouse] No confirmation page found after submit")
        return "requires_human"

    except Exception as exc:
        logger.error(f"[greenhouse] Error applying to {url}: {exc}")
        return "failed"
