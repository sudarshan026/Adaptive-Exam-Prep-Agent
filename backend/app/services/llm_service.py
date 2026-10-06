"""LLM service using Groq API (OpenAI-compatible) via httpx.

Groq provides ultra-fast LLM inference. We use httpx to call the
OpenAI-compatible API directly, avoiding extra dependencies.
"""
import json
import logging
from typing import Optional

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "qwen/qwen3.8-27b"


async def _call_groq(
    headers: dict,
    messages: list,
    model: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> Optional[str]:
    """Make a single call to the Groq API with the given model."""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def call_llm(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    json_mode: bool = False,
) -> Optional[str]:
    """Call the Groq LLM API and return the text response.

    Returns None if the API key is missing (demo mode) or on error.
    Automatically falls back to a secondary model if the primary fails.
    """
    if settings.is_demo_mode:
        logger.debug("LLM call skipped — demo mode (no GROQ_API_KEY)")
        return None

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    models_to_try = [DEFAULT_MODEL, FALLBACK_MODEL]

    for model in models_to_try:
        try:
            text = await _call_groq(headers, messages, model, temperature, max_tokens, json_mode)
            logger.info("LLM call succeeded with model: %s", model)
            return text
        except httpx.HTTPStatusError as e:
            logger.warning(
                "Groq API HTTP error %s with model %s: %s",
                e.response.status_code, model,
                e.response.text[:500],
            )
            # If model is decommissioned/unavailable, try next model
            if e.response.status_code in (400, 404):
                continue
            # For other HTTP errors (rate limit, auth), don't retry with different model
            return None
        except httpx.TimeoutException:
            logger.error("Groq API request timed out with model %s", model)
            continue
        except Exception as e:
            logger.error("Groq API error with model %s: %s", model, e)
            continue

    logger.error("All Groq models failed")
    return None


def extract_json(text: str):
    """Extract JSON from a response that might be wrapped in markdown code blocks."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ```
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        else:
            text = text[3:]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    text = text.strip()
    return json.loads(text)
