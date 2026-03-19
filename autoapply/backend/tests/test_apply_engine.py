"""
Unit tests for the apply engine adapter dispatcher.
Verifies URL routing and fallback behavior without launching a real browser.
"""

import re

import pytest

from services.apply_engine import _ADAPTER_PATTERNS
from services.adapters.greenhouse import apply_greenhouse
from services.adapters.lever import apply_lever
from services.adapters.workday import apply_workday
from services.adapters.icims import apply_icims


class TestAdapterRouting:
    """Verify that URL patterns route to the correct adapter."""

    def _find_adapter(self, url: str):
        for pattern, fn in _ADAPTER_PATTERNS:
            if pattern.search(url):
                return fn
        return None

    def test_greenhouse_url_routes_to_greenhouse(self) -> None:
        url = "https://boards.greenhouse.io/techco/jobs/12345"
        adapter = self._find_adapter(url)
        assert adapter is apply_greenhouse

    def test_lever_url_routes_to_lever(self) -> None:
        url = "https://jobs.lever.co/techco/apply/abcdef"
        adapter = self._find_adapter(url)
        assert adapter is apply_lever

    def test_workday_url_routes_to_workday(self) -> None:
        url = "https://techco.myworkdayjobs.com/en-US/TechCoJobs/job/Senior-Engineer"
        adapter = self._find_adapter(url)
        assert adapter is apply_workday

    def test_icims_url_routes_to_icims(self) -> None:
        url = "https://careers.icims.com/jobs/5678/senior-engineer/job"
        adapter = self._find_adapter(url)
        assert adapter is apply_icims

    def test_unknown_url_returns_none(self) -> None:
        url = "https://unknown-ats.example.com/jobs/apply"
        adapter = self._find_adapter(url)
        assert adapter is None

    def test_workday_alternate_domain(self) -> None:
        url = "https://wd3.myworkdayjobs.com/company/job/role/12345"
        adapter = self._find_adapter(url)
        assert adapter is apply_workday

    def test_all_patterns_compile(self) -> None:
        """All regex patterns in _ADAPTER_PATTERNS are valid."""
        for pattern, fn in _ADAPTER_PATTERNS:
            assert isinstance(pattern, re.Pattern)
            assert callable(fn)
