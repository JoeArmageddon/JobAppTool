"""
Lever ATS adapter.
Handles jobs.lever.co application forms.
"""

import json
import os
import random
from pathlib import Path
from typing import Literal

from loguru import logger
from playwright.async_api import Page

from models.orm import Application

ApplyOutcome = Literal["success", "failed", "requires_human"]

SCREENSHOTS_DIR = Path(os.environ.get("UPLOADS_DIR", "/app/uploads")) / "screenshots"


async def _slow_type(page: Page, selector: str, text: str) -> None:
    await page.click(selector)
    for char in text:
        await page.type(selector, char, delay=random.randint(40, 120))


async def apply_lever(page: Page, application: Application) -> ApplyOutcome:
    """Apply to a Lever job posting."""
    job = application.job
    if not job:
        return "requires_human"

    url = job.source_url
    resume_data = {}
    if application.tailored_resume_text:
        try:
            resume_data = json.loads(application.tailored_resume_text)
        except json.JSONDecodeError:
            pass

    try:
        logger.info(f"[lever] Navigating to {url}")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(random.randint(1000, 2000))

        # Lever forms vary — check for the apply button first
        apply_btn = await page.query_selector("a[href*='/apply'], .postings-btn-submit")
        if apply_btn:
            await apply_btn.click()
            await page.wait_for_timeout(random.randint(1000, 2000))

        # Check we're on an application form
        form = await page.query_selector("form.application-form, #application-form")
        if not form:
            return "requires_human"

        name_field = await page.query_selector("input[name='name']")
        if name_field:
            await _slow_type(page, "input[name='name']", resume_data.get("name", ""))
            await page.wait_for_timeout(random.randint(300, 700))

        email_field = await page.query_selector("input[name='email']")
        if email_field:
            await _slow_type(page, "input[name='email']", resume_data.get("email", ""))
            await page.wait_for_timeout(random.randint(300, 700))

        phone_field = await page.query_selector("input[name='phone']")
        if phone_field:
            await _slow_type(page, "input[name='phone']", resume_data.get("phone", ""))
            await page.wait_for_timeout(random.randint(300, 700))

        # Cover letter
        cl_field = await page.query_selector("textarea[name='comments'], textarea.cover-letter")
        if cl_field and application.cover_letter_text:
            await cl_field.fill(application.cover_letter_text)

        await page.wait_for_timeout(random.randint(1000, 2500))

        # Pre-flight screenshot
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        pre_path = SCREENSHOTS_DIR / f"{application.id}_lever_preflight.png"
        await page.screenshot(path=str(pre_path))

        # Resume upload required — defer to human if no PDF
        resume_upload = await page.query_selector("input[type='file']")
        if resume_upload and not application.tailored_resume_pdf_url:
            return "requires_human"

        # Submit
        submit_btn = await page.query_selector("button[type='submit'], input[type='submit']")
        if not submit_btn:
            return "requires_human"

        await submit_btn.click()
        await page.wait_for_timeout(random.randint(2000, 4000))

        # Check for confirmation
        success = await page.query_selector(".confirmation-message, .thank-you, h1:has-text('Thank')")
        if success:
            confirm_path = SCREENSHOTS_DIR / f"{application.id}_lever_confirm.png"
            await page.screenshot(path=str(confirm_path))
            application.screenshot_url = str(confirm_path)
            logger.info(f"[lever] Successfully applied for application {application.id}")
            return "success"

        return "requires_human"

    except Exception as exc:
        logger.error(f"[lever] Error applying to {url}: {exc}")
        return "failed"
