"""
Apply engine — Playwright-based ATS adapter dispatcher.
Routes applications to the correct adapter based on source URL.

LinkedIn Easy Apply uses a persistent browser context (for session cookies).
All other adapters use a fresh ephemeral context per run.
"""

import os
import random
import re
from pathlib import Path
from typing import Literal

from loguru import logger
from playwright.async_api import async_playwright

from models.orm import Application
from services.adapters.greenhouse import apply_greenhouse
from services.adapters.icims import apply_icims
from services.adapters.lever import apply_lever
from services.adapters.linkedin import apply_linkedin
from services.adapters.workday import apply_workday

ApplyOutcome = Literal["success", "failed", "requires_human"]

# Persistent browser data dir for LinkedIn session cookies
_LINKEDIN_USER_DATA_DIR = str(
    Path(os.environ.get("UPLOADS_DIR", "/app/uploads")) / "linkedin_browser"
)

# URL patterns → adapter (checked in priority order)
# LinkedIn must come before generic patterns since jobspy LinkedIn URLs contain "linkedin.com"
_ADAPTER_PATTERNS: list[tuple[re.Pattern, callable]] = [
    (re.compile(r"linkedin\.com/jobs", re.IGNORECASE), apply_linkedin),
    (re.compile(r"greenhouse\.io", re.IGNORECASE), apply_greenhouse),
    (re.compile(r"lever\.co", re.IGNORECASE), apply_lever),
    (re.compile(r"myworkdayjobs\.com|workday\.com", re.IGNORECASE), apply_workday),
    (re.compile(r"icims\.com", re.IGNORECASE), apply_icims),
]

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


async def apply_to_job(application: Application) -> ApplyOutcome:
    """
    Dispatch the application to the correct ATS adapter.
    Falls back to 'requires_human' if no adapter matches.

    LinkedIn uses a persistent context so session cookies survive across runs.
    All other adapters use a fresh ephemeral context.
    """
    job = application.job
    if not job or not job.source_url:
        logger.warning(f"[apply_engine] No source URL for application {application.id}")
        return "requires_human"

    url = job.source_url
    adapter_fn = None
    for pattern, fn in _ADAPTER_PATTERNS:
        if pattern.search(url):
            adapter_fn = fn
            break

    if adapter_fn is None:
        logger.info(f"[apply_engine] No adapter for URL {url}, requires human")
        return "requires_human"

    async with async_playwright() as pw:
        is_linkedin = adapter_fn is apply_linkedin

        if is_linkedin:
            # Persistent context preserves LinkedIn session cookies across restarts
            Path(_LINKEDIN_USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
            context = await pw.chromium.launch_persistent_context(
                user_data_dir=_LINKEDIN_USER_DATA_DIR,
                headless=True,
                user_agent=_USER_AGENT,
                viewport={"width": 1280, "height": 800},
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.pages[0] if context.pages else await context.new_page()
        else:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                user_agent=_USER_AGENT,
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

        try:
            # Random initial delay (anti-detection)
            await page.wait_for_timeout(random.randint(500, 1500))

            outcome = await adapter_fn(page, application)
            logger.info(f"[apply_engine] {url} → {outcome} for app {application.id}")
            return outcome

        except Exception as exc:
            logger.error(f"[apply_engine] Error applying to {url}: {exc}")
            return "failed"

        finally:
            if is_linkedin:
                await context.close()
            else:
                await context.browser.close()
