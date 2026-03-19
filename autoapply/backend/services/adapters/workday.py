"""
Workday ATS adapter.
Handles myworkdayjobs.com and workday.com application forms.

Workday is the most complex ATS — multi-step wizard, heavy JS, frequent
bot-detection. We detect the form, fill what we can, and fall back to
requires_human for any step we cannot handle automatically.
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

# Workday URL patterns
WORKDAY_DOMAINS = ("myworkdayjobs.com", "workday.com", "wd1.myworkdayjobs", "wd3.myworkdayjobs")


def _is_workday_url(url: str) -> bool:
    return any(domain in url for domain in WORKDAY_DOMAINS)


async def _slow_type(page: Page, selector: str, text: str) -> None:
    """Type with human-like random delays between keystrokes."""
    await page.click(selector)
    for char in text:
        await page.type(selector, char, delay=random.randint(40, 120))


async def _fill_if_present(page: Page, selector: str, value: str) -> bool:
    """Fill a field if it exists. Returns True if field was found and filled."""
    el = await page.query_selector(selector)
    if el and value:
        await _slow_type(page, selector, value)
        await page.wait_for_timeout(random.randint(300, 700))
        return True
    return False


async def _click_apply_button(page: Page) -> bool:
    """Find and click the initial 'Apply' button if on a job detail page."""
    apply_selectors = [
        "a[data-uxi-element-id='applyButton']",
        "a[href*='apply']",
        "button[aria-label*='Apply']",
        "a[aria-label*='Apply']",
        "[data-automation-id='applyButton']",
        "a:has-text('Apply Now')",
        "button:has-text('Apply Now')",
        "a:has-text('Apply')",
    ]
    for sel in apply_selectors:
        btn = await page.query_selector(sel)
        if btn:
            await btn.click()
            await page.wait_for_timeout(random.randint(1500, 2500))
            return True
    return False


async def _detect_workday_form(page: Page) -> bool:
    """Check if there is a Workday application form on the page."""
    indicators = [
        "[data-automation-id='createAccountForm']",
        "[data-automation-id='applyManually']",
        "[data-automation-id='legalNameSection']",
        "div[class*='WDAY']",
        "div[class*='wd-']",
        "form[action*='workday']",
        "input[data-automation-id='legalNameSection_firstName']",
    ]
    for sel in indicators:
        el = await page.query_selector(sel)
        if el:
            return True
    return False


async def _fill_personal_info(page: Page, resume_data: dict) -> None:
    """Fill the personal information step in Workday."""
    name = resume_data.get("name", "")
    name_parts = name.split() if name else []
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    email = resume_data.get("email", "")
    phone = resume_data.get("phone", "")

    # Workday uses data-automation-id attributes
    first_selectors = [
        "input[data-automation-id='legalNameSection_firstName']",
        "input[aria-label*='First Name']",
        "input[name*='firstName']",
        "#firstName",
    ]
    last_selectors = [
        "input[data-automation-id='legalNameSection_lastName']",
        "input[aria-label*='Last Name']",
        "input[name*='lastName']",
        "#lastName",
    ]
    email_selectors = [
        "input[data-automation-id='email']",
        "input[type='email']",
        "input[aria-label*='Email']",
        "#email",
    ]
    phone_selectors = [
        "input[data-automation-id='phone-number']",
        "input[type='tel']",
        "input[aria-label*='Phone']",
        "#phone",
    ]

    for sel in first_selectors:
        if await _fill_if_present(page, sel, first_name):
            break

    for sel in last_selectors:
        if await _fill_if_present(page, sel, last_name):
            break

    for sel in email_selectors:
        if await _fill_if_present(page, sel, email):
            break

    for sel in phone_selectors:
        if await _fill_if_present(page, sel, phone):
            break


async def _advance_to_next_step(page: Page) -> bool:
    """Click the Next/Save & Continue button in the Workday wizard."""
    next_selectors = [
        "button[data-automation-id='bottom-navigation-next-button']",
        "button[aria-label='Next']",
        "button:has-text('Next')",
        "button:has-text('Save & Continue')",
        "button:has-text('Continue')",
    ]
    for sel in next_selectors:
        btn = await page.query_selector(sel)
        if btn:
            await btn.click()
            await page.wait_for_timeout(random.randint(1500, 2500))
            return True
    return False


async def _submit_application(page: Page) -> bool:
    """Click the final submit button."""
    submit_selectors = [
        "button[data-automation-id='bottom-navigation-next-button']",
        "button[aria-label='Submit']",
        "button:has-text('Submit')",
        "input[type='submit']",
    ]
    for sel in submit_selectors:
        btn = await page.query_selector(sel)
        if btn:
            await btn.click()
            await page.wait_for_timeout(random.randint(2000, 4000))
            return True
    return False


async def _check_success(page: Page) -> bool:
    """Check for a Workday confirmation/success page."""
    success_selectors = [
        "[data-automation-id='applicationSubmitted']",
        ".applicationSubmitted",
        "h1:has-text('Thank you')",
        "h2:has-text('Thank you')",
        "p:has-text('application has been submitted')",
        "p:has-text('successfully submitted')",
        "[data-automation-id='confirmationPanel']",
    ]
    for sel in success_selectors:
        el = await page.query_selector(sel)
        if el:
            return True
    return False


async def apply_workday(page: Page, application: Application) -> ApplyOutcome:
    """
    Apply to a Workday job posting.

    Workday is a multi-step wizard. We:
    1. Navigate to the job page
    2. Click the Apply button
    3. Detect the Workday form
    4. Fill personal info (step 1)
    5. Advance through steps — fall back to requires_human if we hit
       a step we cannot handle (assessments, complex custom questions)
    6. Submit and confirm

    Returns success | failed | requires_human.
    """
    job = application.job
    if not job:
        return "requires_human"

    url = job.source_url
    if not url:
        return "requires_human"

    if not _is_workday_url(url):
        logger.warning(f"[workday] URL does not look like Workday: {url}")
        return "requires_human"

    resume_data: dict = {}
    if application.tailored_resume_text:
        try:
            resume_data = json.loads(application.tailored_resume_text)
        except json.JSONDecodeError:
            pass

    try:
        logger.info(f"[workday] Navigating to {url}")
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(random.randint(1500, 2500))

        # Workday job pages have an Apply button — click it to open the form
        clicked = await _click_apply_button(page)
        if clicked:
            # May open in a new tab or navigate
            await page.wait_for_timeout(random.randint(2000, 3000))

        # If new tab opened, switch to it
        context = page.context
        pages = context.pages
        if len(pages) > 1:
            page = pages[-1]
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(random.randint(1000, 2000))

        # Verify we have a Workday form
        if not await _detect_workday_form(page):
            logger.info(f"[workday] No Workday form detected, deferring to human")
            return "requires_human"

        # Pre-form screenshot
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        pre_path = SCREENSHOTS_DIR / f"{application.id}_workday_start.png"
        await page.screenshot(path=str(pre_path))

        # Step 1: Fill personal information
        await _fill_personal_info(page, resume_data)
        await page.wait_for_timeout(random.randint(500, 1000))

        # Resume upload — if file input present and we have a PDF, upload it
        resume_upload = await page.query_selector(
            "input[type='file'][data-automation-id*='resume'], "
            "input[type='file'][aria-label*='Resume'], "
            "input[type='file'][aria-label*='CV']"
        )
        if resume_upload:
            if application.tailored_resume_pdf_url and os.path.exists(
                application.tailored_resume_pdf_url
            ):
                await resume_upload.set_input_files(application.tailored_resume_pdf_url)
                await page.wait_for_timeout(random.randint(1000, 2000))
            else:
                logger.info(f"[workday] Resume upload required but no PDF available")
                return "requires_human"

        # Cover letter — if text area present
        cl_field = await page.query_selector(
            "textarea[data-automation-id='coverLetter'], "
            "textarea[aria-label*='Cover Letter'], "
            "textarea[aria-label*='cover letter']"
        )
        if cl_field and application.cover_letter_text:
            await cl_field.fill(application.cover_letter_text)
            await page.wait_for_timeout(random.randint(300, 700))

        # Pre-submit screenshot
        preflight_path = SCREENSHOTS_DIR / f"{application.id}_workday_preflight.png"
        await page.screenshot(path=str(preflight_path))

        # Attempt to advance through wizard steps (max 5 steps)
        max_steps = 5
        for step_num in range(max_steps):
            # Check if we're already at submission
            already_success = await _check_success(page)
            if already_success:
                break

            # Look for submit button before trying next
            submit_btn = await page.query_selector(
                "button[data-automation-id='bottom-navigation-next-button']"
            )
            current_text = ""
            if submit_btn:
                current_text = (await submit_btn.inner_text()).strip().lower()

            if "submit" in current_text:
                advanced = await _submit_application(page)
            else:
                advanced = await _advance_to_next_step(page)

            if not advanced:
                logger.info(f"[workday] Could not advance at step {step_num + 1}")
                return "requires_human"

            # Detect if we've hit a step we cannot handle (assessments, etc.)
            assessment = await page.query_selector(
                "[data-automation-id='assessmentSection'], "
                "div:has-text('Assessment'), "
                "div:has-text('questionnaire')"
            )
            if assessment:
                logger.info(f"[workday] Assessment/questionnaire detected — requires human")
                return "requires_human"

        # Final success check
        if await _check_success(page):
            confirm_path = SCREENSHOTS_DIR / f"{application.id}_workday_confirm.png"
            await page.screenshot(path=str(confirm_path))
            application.screenshot_url = str(confirm_path)
            logger.info(f"[workday] Successfully applied for application {application.id}")
            return "success"

        logger.warning(f"[workday] Could not confirm submission for application {application.id}")
        return "requires_human"

    except Exception as exc:
        logger.error(f"[workday] Error applying to {url}: {exc}")
        return "failed"
