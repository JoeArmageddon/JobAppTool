"""
Apply engine — Playwright-based ATS adapter dispatcher.
Routes applications to the correct adapter based on source URL.
"""

import random
import re
from typing import Literal

from loguru import logger
from playwright.async_api import async_playwright

from models.orm import Application
from services.adapters.greenhouse import apply_greenhouse
from services.adapters.lever import apply_lever

ApplyOutcome = Literal["success", "failed", "requires_human"]

# URL patterns → adapter
_ADAPTER_PATTERNS: list[tuple[re.Pattern, callable]] = [
    (re.compile(r"greenhouse\.io", re.IGNORECASE), apply_greenhouse),
    (re.compile(r"lever\.co", re.IGNORECASE), apply_lever),
]


async def apply_to_job(application: Application) -> ApplyOutcome:
    """
    Dispatch the application to the correct ATS adapter.
    Falls back to 'requires_human' if no adapter matches.
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
        browser = await pw.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

            # Random initial delay (anti-detection)
            await page.wait_for_timeout(random.randint(500, 1500))

            outcome = await adapter_fn(page, application)
            logger.info(f"[apply_engine] {url} → {outcome} for app {application.id}")
            return outcome
        except Exception as exc:
            logger.error(f"[apply_engine] Error applying to {url}: {exc}")
            return "failed"
        finally:
            await browser.close()
