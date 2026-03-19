"""
iCIMS ATS adapter.
Handles careers.icims.com application forms.

iCIMS uses a multi-page form with iframe-based steps on some installations.
We handle the most common flow: personal info → resume upload → submit.
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

ICIMS_DOMAINS = ("icims.com", "careers.icims.com")


def _is_icims_url(url: str) -> bool:
    return any(domain in url for domain in ICIMS_DOMAINS)


async def _slow_type(page: Page, selector: str, text: str) -> None:
    """Type with human-like random delays between keystrokes."""
    await page.click(selector)
    for char in text:
        await page.type(selector, char, delay=random.randint(40, 120))


async def _fill_if_present(page: Page, selector: str, value: str) -> bool:
    """Fill a field if it exists. Returns True if filled."""
    el = await page.query_selector(selector)
    if el and value:
        await _slow_type(page, selector, value)
        await page.wait_for_timeout(random.randint(300, 700))
        return True
    return False


async def _click_apply_button(page: Page) -> bool:
    """Click the Apply Now / Apply button on the job detail page."""
    selectors = [
        "a:has-text('Apply Now')",
        "a:has-text('Apply for Job')",
        "button:has-text('Apply Now')",
        "input[value='Apply Now']",
        "a[href*='apply']",
        ".iCIMS_Anchor",
        "#applyButton",
    ]
    for sel in selectors:
        btn = await page.query_selector(sel)
        if btn:
            await btn.click()
            await page.wait_for_timeout(random.randint(1500, 2500))
            return True
    return False


async def _detect_icims_form(page: Page) -> bool:
    """Detect whether we're on an iCIMS application form."""
    indicators = [
        ".iCIMS_InputField",
        "#iCIMS_Header",
        "form[action*='icims']",
        "[name='iCIMS_form']",
        ".icims-widget",
        "input[name='input1']",  # iCIMS classic field naming
        ".iCIMS_ButtonRow",
    ]
    for sel in indicators:
        el = await page.query_selector(sel)
        if el:
            return True
    return False


async def _fill_personal_info(page: Page, resume_data: dict) -> None:
    """Fill personal info fields for iCIMS forms."""
    name = resume_data.get("name", "")
    name_parts = name.split() if name else []
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    email = resume_data.get("email", "")
    phone = resume_data.get("phone", "")

    # iCIMS field selectors (varies by customer config)
    first_selectors = [
        "input[id*='firstname' i]",
        "input[name*='firstname' i]",
        "input[id*='first_name' i]",
        "input[placeholder*='First Name' i]",
        "#firstname",
    ]
    last_selectors = [
        "input[id*='lastname' i]",
        "input[name*='lastname' i]",
        "input[id*='last_name' i]",
        "input[placeholder*='Last Name' i]",
        "#lastname",
    ]
    email_selectors = [
        "input[type='email']",
        "input[id*='email' i]",
        "input[name*='email' i]",
        "input[placeholder*='Email' i]",
    ]
    phone_selectors = [
        "input[type='tel']",
        "input[id*='phone' i]",
        "input[name*='phone' i]",
        "input[placeholder*='Phone' i]",
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


async def _handle_resume_upload(page: Page, application: Application) -> bool:
    """
    Handle resume upload. Returns True if upload succeeded or no upload needed.
    Returns False if upload is required but we can't complete it.
    """
    file_input = await page.query_selector("input[type='file']")
    if not file_input:
        return True  # No upload required

    pdf_path = application.tailored_resume_pdf_url
    if pdf_path and os.path.exists(pdf_path):
        await file_input.set_input_files(pdf_path)
        await page.wait_for_timeout(random.randint(1000, 2000))
        return True

    return False  # Upload required but no PDF available


async def _fill_cover_letter(page: Page, application: Application) -> None:
    """Fill cover letter if a text area is present."""
    cl_selectors = [
        "textarea[id*='cover' i]",
        "textarea[name*='cover' i]",
        "textarea[placeholder*='Cover Letter' i]",
        "textarea[aria-label*='Cover Letter' i]",
    ]
    if not application.cover_letter_text:
        return
    for sel in cl_selectors:
        el = await page.query_selector(sel)
        if el:
            await el.fill(application.cover_letter_text)
            await page.wait_for_timeout(random.randint(300, 700))
            break


async def _advance_step(page: Page) -> bool:
    """Click the Next button in iCIMS multi-step form."""
    next_selectors = [
        "input[value='Next']",
        "input[value='Continue']",
        "button:has-text('Next')",
        "button:has-text('Continue')",
        ".iCIMS_Button_Next",
        "a.iCIMS_Anchor:has-text('Next')",
    ]
    for sel in next_selectors:
        btn = await page.query_selector(sel)
        if btn:
            await btn.click()
            await page.wait_for_timeout(random.randint(1500, 2500))
            return True
    return False


async def _submit(page: Page) -> bool:
    """Click the final Submit button."""
    submit_selectors = [
        "input[value='Submit']",
        "input[value='Submit Application']",
        "button:has-text('Submit')",
        "button[type='submit']",
        ".iCIMS_Button_Submit",
    ]
    for sel in submit_selectors:
        btn = await page.query_selector(sel)
        if btn:
            await btn.click()
            await page.wait_for_timeout(random.randint(2000, 4000))
            return True
    return False


async def _check_success(page: Page) -> bool:
    """Check for iCIMS confirmation page indicators."""
    success_indicators = [
        ".iCIMS_SuccessMessage",
        "h1:has-text('Thank you')",
        "h2:has-text('Thank you')",
        "p:has-text('application has been submitted')",
        "p:has-text('successfully applied')",
        "p:has-text('Application Submitted')",
        ".confirmation",
    ]
    for sel in success_indicators:
        el = await page.query_selector(sel)
        if el:
            return True
    return False


async def apply_icims(page: Page, application: Application) -> ApplyOutcome:
    """
    Apply to an iCIMS job posting.

    Flow:
    1. Navigate to job URL
    2. Click Apply button
    3. Detect iCIMS form
    4. Fill personal info
    5. Handle resume upload (requires PDF)
    6. Fill cover letter if present
    7. Navigate through steps (max 4)
    8. Submit and confirm

    Returns success | failed | requires_human.
    """
    job = application.job
    if not job:
        return "requires_human"

    url = job.source_url
    if not url:
        return "requires_human"

    if not _is_icims_url(url):
        logger.warning(f"[icims] URL does not look like iCIMS: {url}")
        return "requires_human"

    resume_data: dict = {}
    if application.tailored_resume_text:
        try:
            resume_data = json.loads(application.tailored_resume_text)
        except json.JSONDecodeError:
            pass

    try:
        logger.info(f"[icims] Navigating to {url}")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(random.randint(1000, 2000))

        # Try to click an Apply button on the job listing page
        await _click_apply_button(page)

        # Handle potential new tab
        context = page.context
        pages = context.pages
        if len(pages) > 1:
            page = pages[-1]
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(random.randint(1000, 2000))

        # Verify we have an iCIMS form
        if not await _detect_icims_form(page):
            logger.info(f"[icims] No iCIMS form detected at {url}")
            return "requires_human"

        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        start_path = SCREENSHOTS_DIR / f"{application.id}_icims_start.png"
        await page.screenshot(path=str(start_path))

        # Fill personal information
        await _fill_personal_info(page, resume_data)

        # Handle resume upload
        upload_ok = await _handle_resume_upload(page, application)
        if not upload_ok:
            logger.info(f"[icims] Resume upload required but no PDF available")
            return "requires_human"

        # Fill cover letter
        await _fill_cover_letter(page, application)

        await page.wait_for_timeout(random.randint(500, 1000))

        # Pre-submit screenshot
        preflight_path = SCREENSHOTS_DIR / f"{application.id}_icims_preflight.png"
        await page.screenshot(path=str(preflight_path))

        # Navigate through wizard steps (max 4)
        max_steps = 4
        for step_num in range(max_steps):
            if await _check_success(page):
                break

            # Check if there's a submit button on this step
            submit_btn = await page.query_selector(
                "input[value='Submit'], input[value='Submit Application'], "
                "button:has-text('Submit')"
            )
            if submit_btn:
                submitted = await _submit(page)
                if not submitted:
                    return "requires_human"
                break

            # Otherwise advance to next step
            advanced = await _advance_step(page)
            if not advanced:
                # No next or submit — might already be on the last fillable page
                submitted = await _submit(page)
                if not submitted:
                    logger.info(
                        f"[icims] Cannot advance or submit at step {step_num + 1}"
                    )
                    return "requires_human"
                break

            # After advancing, fill any new personal info fields that appear
            await _fill_personal_info(page, resume_data)
            await _fill_cover_letter(page, application)

        # Check final success
        if await _check_success(page):
            confirm_path = SCREENSHOTS_DIR / f"{application.id}_icims_confirm.png"
            await page.screenshot(path=str(confirm_path))
            application.screenshot_url = str(confirm_path)
            logger.info(f"[icims] Successfully applied for application {application.id}")
            return "success"

        logger.warning(f"[icims] Could not confirm submission for application {application.id}")
        return "requires_human"

    except Exception as exc:
        logger.error(f"[icims] Error applying to {url}: {exc}")
        return "failed"
