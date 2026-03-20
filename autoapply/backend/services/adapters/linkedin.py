"""
LinkedIn Easy Apply adapter.

LinkedIn requires an authenticated session. Credentials are read from:
  LINKEDIN_EMAIL    — your LinkedIn login email
  LINKEDIN_PASSWORD — your LinkedIn login password

Session cookies are persisted to UPLOADS_DIR/linkedin_session.json so the
adapter logs in once and reuses the session across runs. If the session
expires, it re-authenticates automatically.

Anti-detection notes:
  - playwright-stealth is applied in apply_engine before this is called
  - All typing uses per-keystroke random delays
  - Random pauses between every action
  - Only clicks "Easy Apply" — never the external "Apply" button
  - Returns requires_human for multi-question screening forms we can't answer
"""

import json
import os
import random
from pathlib import Path
from typing import Literal

from loguru import logger
from playwright.async_api import BrowserContext, Page

from models.orm import Application

ApplyOutcome = Literal["success", "failed", "requires_human"]

SCREENSHOTS_DIR = Path(os.environ.get("UPLOADS_DIR", "/app/uploads")) / "screenshots"
SESSION_FILE = Path(os.environ.get("UPLOADS_DIR", "/app/uploads")) / "linkedin_session.json"

LINKEDIN_EMAIL = os.environ.get("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.environ.get("LINKEDIN_PASSWORD", "")

# Selectors — LinkedIn updates their DOM frequently; ordered by reliability
_EASY_APPLY_BTN = [
    "button.jobs-apply-button[aria-label*='Easy Apply']",
    "button[aria-label*='Easy Apply']",
    ".jobs-apply-button--top-card",
    "button:has-text('Easy Apply')",
]

_NEXT_BTN = [
    "button[aria-label='Continue to next step']",
    "button[aria-label='Review your application']",
    "footer button.artdeco-button--primary",
    "button:has-text('Next')",
    "button:has-text('Review')",
]

_SUBMIT_BTN = [
    "button[aria-label='Submit application']",
    "button:has-text('Submit application')",
    "button:has-text('Submit')",
]

_SUCCESS_INDICATORS = [
    "div[aria-label='Your application was sent']",
    "h2:has-text('Your application was sent')",
    "p:has-text('application was sent')",
    ".artdeco-toast-item--success",
    "div:has-text('applied')",
]

_LOGIN_INDICATORS = [
    "#username",
    "input[name='session_key']",
    "a[href*='/login']",
]


async def _slow_type(page: Page, selector: str, text: str) -> None:
    await page.click(selector)
    await page.wait_for_timeout(random.randint(100, 300))
    for char in text:
        await page.type(selector, char, delay=random.randint(50, 150))


async def _click_first(page: Page, selectors: list[str]) -> bool:
    """Try each selector in order, click the first that exists. Returns True if clicked."""
    for sel in selectors:
        el = await page.query_selector(sel)
        if el:
            await el.click()
            await page.wait_for_timeout(random.randint(800, 1500))
            return True
    return False


async def _is_logged_in(page: Page) -> bool:
    """Check if the current page shows a logged-in LinkedIn session."""
    # Feed, jobs, or profile pages — if we see the nav, we're in
    nav = await page.query_selector(
        "nav.global-nav, [data-test-global-nav], .global-nav__me-photo"
    )
    return nav is not None


async def _load_session(context: BrowserContext) -> bool:
    """Load persisted cookies into the browser context. Returns True if cookies existed."""
    if not SESSION_FILE.exists():
        return False
    try:
        cookies = json.loads(SESSION_FILE.read_text())
        await context.add_cookies(cookies)
        logger.info("[linkedin] Loaded persisted session cookies")
        return True
    except Exception as exc:
        logger.warning(f"[linkedin] Could not load session cookies: {exc}")
        return False


async def _save_session(context: BrowserContext) -> None:
    """Persist current cookies to disk for the next run."""
    try:
        cookies = await context.cookies()
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        SESSION_FILE.write_text(json.dumps(cookies, indent=2))
        logger.info("[linkedin] Session cookies saved")
    except Exception as exc:
        logger.warning(f"[linkedin] Could not save session cookies: {exc}")


async def _login(page: Page, context: BrowserContext) -> bool:
    """
    Perform LinkedIn login using LINKEDIN_EMAIL / LINKEDIN_PASSWORD.
    Returns True if login succeeded.
    """
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        logger.error(
            "[linkedin] LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set to use Easy Apply"
        )
        return False

    try:
        logger.info("[linkedin] Navigating to login page")
        await page.goto("https://www.linkedin.com/login", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(random.randint(1000, 2000))

        # Fill email
        await _slow_type(page, "#username", LINKEDIN_EMAIL)
        await page.wait_for_timeout(random.randint(500, 1000))

        # Fill password
        await _slow_type(page, "#password", LINKEDIN_PASSWORD)
        await page.wait_for_timeout(random.randint(500, 1000))

        # Click sign in
        await page.click("button[type='submit']")
        await page.wait_for_timeout(random.randint(3000, 5000))

        # Check for CAPTCHA or security challenge
        challenge = await page.query_selector(
            "[id*='captcha'], .challenge-dialog, input[name='pin']"
        )
        if challenge:
            logger.warning("[linkedin] Security challenge detected — cannot auto-login")
            return False

        if await _is_logged_in(page):
            await _save_session(context)
            logger.info("[linkedin] Login successful")
            return True

        logger.warning("[linkedin] Login may have failed — could not confirm session")
        return False

    except Exception as exc:
        logger.error(f"[linkedin] Login error: {exc}")
        return False


async def _ensure_authenticated(page: Page, context: BrowserContext) -> bool:
    """
    Ensure we have a valid LinkedIn session.
    Tries saved cookies first, falls back to fresh login.
    """
    # Try loading saved cookies
    had_cookies = await _load_session(context)

    if had_cookies:
        # Quick check — visit feed to confirm session is still valid
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(random.randint(1000, 2000))
        if await _is_logged_in(page):
            return True
        logger.info("[linkedin] Saved session expired — re-authenticating")

    return await _login(page, context)


async def _fill_contact_info(page: Page, resume_data: dict) -> None:
    """Fill any contact info fields LinkedIn shows in the Easy Apply modal."""
    name = resume_data.get("name", "")
    parts = name.split() if name else []
    first = parts[0] if parts else ""
    last = " ".join(parts[1:]) if len(parts) > 1 else ""
    email = resume_data.get("email", "")
    phone = resume_data.get("phone", "")

    field_map = [
        (["input[id*='firstName' i]", "input[placeholder*='First name' i]"], first),
        (["input[id*='lastName' i]", "input[placeholder*='Last name' i]"], last),
        (["input[id*='phoneNumber' i]", "input[placeholder*='Phone' i]", "input[type='tel']"], phone),
        (["input[id*='email' i]", "input[type='email']"], email),
    ]

    for selectors, value in field_map:
        if not value:
            continue
        for sel in selectors:
            el = await page.query_selector(sel)
            if el:
                current = await el.input_value()
                if not current:  # Only fill if empty — don't overwrite LinkedIn's pre-fill
                    await _slow_type(page, sel, value)
                    await page.wait_for_timeout(random.randint(200, 500))
                break


async def _handle_resume_upload(page: Page, application: Application) -> bool:
    """
    Upload resume PDF if a file input is present.
    Returns True if upload succeeded or no upload needed.
    """
    file_input = await page.query_selector(
        "input[type='file'][name*='resume' i], "
        "input[type='file'][id*='resume' i], "
        "input[type='file']"
    )
    if not file_input:
        return True  # No upload needed on this step

    pdf_path = application.tailored_resume_pdf_url
    if pdf_path and os.path.exists(pdf_path):
        await file_input.set_input_files(pdf_path)
        await page.wait_for_timeout(random.randint(1500, 2500))
        logger.info("[linkedin] Resume uploaded")
        return True

    # File input present but no PDF — we can't proceed
    logger.info("[linkedin] File upload required but no PDF available")
    return False


async def _detect_screening_questions(page: Page) -> bool:
    """
    Detect if the current step has free-text screening questions we can't answer.
    Dropdowns and yes/no are fine; open-ended text questions require human review.
    """
    # Look for textarea inputs (free-text answers)
    textareas = await page.query_selector_all("textarea")
    for ta in textareas:
        label = await ta.get_attribute("placeholder") or ""
        if label:
            logger.info(f"[linkedin] Free-text screening question detected: '{label[:60]}'")
            return True

    # Look for unbounded text inputs that aren't contact fields
    inputs = await page.query_selector_all(
        "input[type='text']:not([id*='name' i]):not([id*='phone' i]):not([id*='email' i])"
    )
    if len(inputs) > 3:
        logger.info(f"[linkedin] {len(inputs)} unrecognised text inputs — deferring to human")
        return True

    return False


async def apply_linkedin(page: Page, application: Application) -> ApplyOutcome:
    """
    Apply via LinkedIn Easy Apply.

    Flow:
    1. Ensure authenticated (cookie restore → re-login if needed)
    2. Navigate to the LinkedIn job page
    3. Confirm the "Easy Apply" button exists (skip if only external Apply)
    4. Click Easy Apply → handle multi-step modal
    5. Fill contact info, upload resume, handle simple dropdowns
    6. Defer to requires_human if free-text screening questions appear
    7. Submit and confirm

    Returns success | failed | requires_human.
    """
    job = application.job
    if not job or not job.source_url:
        return "requires_human"

    url = job.source_url
    if "linkedin.com" not in url:
        logger.warning(f"[linkedin] URL is not a LinkedIn job: {url}")
        return "requires_human"

    resume_data: dict = {}
    if application.tailored_resume_text:
        try:
            resume_data = json.loads(application.tailored_resume_text)
        except json.JSONDecodeError:
            pass

    try:
        # Auth — uses the page's browser context
        context = page.context
        authed = await _ensure_authenticated(page, context)
        if not authed:
            logger.warning("[linkedin] Could not authenticate — requires human")
            return "requires_human"

        # Navigate to job
        logger.info(f"[linkedin] Navigating to {url}")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(random.randint(1500, 2500))

        # Confirm there's an Easy Apply button (not just an external Apply)
        easy_apply_btn = None
        for sel in _EASY_APPLY_BTN:
            easy_apply_btn = await page.query_selector(sel)
            if easy_apply_btn:
                break

        if not easy_apply_btn:
            logger.info(f"[linkedin] No Easy Apply button on {url} — requires human")
            return "requires_human"

        # Screenshot before we start
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        await page.screenshot(
            path=str(SCREENSHOTS_DIR / f"{application.id}_linkedin_start.png")
        )

        # Click Easy Apply
        await easy_apply_btn.click()
        await page.wait_for_timeout(random.randint(1500, 2500))

        # Step through the modal (max 6 steps)
        max_steps = 6
        for step_num in range(max_steps):
            # Check for success on any step
            for sel in _SUCCESS_INDICATORS:
                if await page.query_selector(sel):
                    confirm_path = SCREENSHOTS_DIR / f"{application.id}_linkedin_confirm.png"
                    await page.screenshot(path=str(confirm_path))
                    application.screenshot_url = str(confirm_path)
                    logger.info(f"[linkedin] Successfully applied for application {application.id}")
                    return "success"

            # Fill contact fields on this step
            await _fill_contact_info(page, resume_data)

            # Handle resume upload
            upload_ok = await _handle_resume_upload(page, application)
            if not upload_ok:
                return "requires_human"

            # Detect screening questions we can't answer
            if await _detect_screening_questions(page):
                await page.screenshot(
                    path=str(SCREENSHOTS_DIR / f"{application.id}_linkedin_screening.png")
                )
                return "requires_human"

            await page.wait_for_timeout(random.randint(500, 1000))

            # Try submit first (last step), then next
            submitted = await _click_first(page, _SUBMIT_BTN)
            if submitted:
                await page.wait_for_timeout(random.randint(2000, 3500))
                # Check success after submit
                for sel in _SUCCESS_INDICATORS:
                    if await page.query_selector(sel):
                        confirm_path = SCREENSHOTS_DIR / f"{application.id}_linkedin_confirm.png"
                        await page.screenshot(path=str(confirm_path))
                        application.screenshot_url = str(confirm_path)
                        logger.info(
                            f"[linkedin] Successfully applied for application {application.id}"
                        )
                        return "success"
                # Submitted but no confirmation detected
                break

            advanced = await _click_first(page, _NEXT_BTN)
            if not advanced:
                logger.info(f"[linkedin] Cannot advance at step {step_num + 1}")
                break

        logger.warning(f"[linkedin] Could not confirm Easy Apply submission for {application.id}")
        return "requires_human"

    except Exception as exc:
        logger.error(f"[linkedin] Error applying to {url}: {exc}")
        return "failed"
