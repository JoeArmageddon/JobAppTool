"""
Unified LLM client — supports Anthropic Claude (recommended) and Groq (free).

Provider is selected via the LLM_PROVIDER environment variable:
  LLM_PROVIDER=anthropic  (default) — requires ANTHROPIC_API_KEY
  LLM_PROVIDER=groq       (free)    — requires GROQ_API_KEY

Model overrides (optional):
  ANTHROPIC_MODEL=claude-sonnet-4-20250514   (default)
  GROQ_MODEL=llama-3.3-70b-versatile         (default)

All services call complete() — provider routing is transparent to callers.
"""

import os
from typing import Literal

from loguru import logger

Provider = Literal["anthropic", "groq"]


def _provider() -> Provider:
    val = os.environ.get("LLM_PROVIDER", "anthropic").strip().lower()
    if val not in ("anthropic", "groq"):
        raise ValueError(
            f"LLM_PROVIDER='{val}' is invalid. Use 'anthropic' or 'groq'."
        )
    return val  # type: ignore[return-value]


def _anthropic_model() -> str:
    return os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


def _groq_model() -> str:
    return os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


async def complete(prompt: str, max_tokens: int = 2048) -> str:
    """
    Send a single-turn prompt and return the response text.

    Raises RuntimeError on API failure — callers should catch this and
    surface a clean message to the user.
    """
    provider = _provider()

    if provider == "anthropic":
        return await _complete_anthropic(prompt, max_tokens)
    else:
        return await _complete_groq(prompt, max_tokens)


async def _complete_anthropic(prompt: str, max_tokens: int) -> str:
    import anthropic

    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model=_anthropic_model(),
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except anthropic.APIError as exc:
        logger.error(f"Anthropic API error: {exc}")
        raise RuntimeError(f"AI service (Anthropic) temporarily unavailable: {exc}") from exc
    except KeyError:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. "
            "Set LLM_PROVIDER=groq and GROQ_API_KEY to use Groq instead."
        )


async def _complete_groq(prompt: str, max_tokens: int) -> str:
    try:
        from groq import Groq
    except ImportError as exc:
        raise RuntimeError(
            "Groq package not installed. Run: pip install groq"
        ) from exc

    try:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        resp = client.chat.completions.create(
            model=_groq_model(),
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        # Groq raises openai-compatible errors
        logger.error(f"Groq API error: {exc}")
        raise RuntimeError(f"AI service (Groq) temporarily unavailable: {exc}") from exc
    except KeyError:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at console.groq.com."
        )
