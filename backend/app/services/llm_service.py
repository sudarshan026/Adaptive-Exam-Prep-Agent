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
DEFAULT_MODEL = "openai/gpt-oss-20b"
FALLBACK_MODEL = "openai/gpt-oss-120b"
ADDITIONAL_MODELS = ["qwen/qwen3.8-27b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]


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
            timeout=30.0,
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
    key = settings.effective_groq_key
    if not key:
        print("[LLM Service] Skipped: No GROQ_API_KEY found in settings or environment.", flush=True)
        return None

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    models_to_try = [DEFAULT_MODEL, FALLBACK_MODEL] + ADDITIONAL_MODELS

    for model in models_to_try:
        try:
            print(f"[LLM Service] Calling Groq with model: {model}...", flush=True)
            text = await _call_groq(headers, messages, model, temperature, max_tokens, json_mode)
            print(f"[LLM Service] Success with model: {model}!", flush=True)
            return text
        except httpx.HTTPStatusError as e:
            print(f"[LLM Service] HTTP error {e.response.status_code} with model {model}: {e.response.text[:200]}", flush=True)
            # If model is unavailable (400, 404) or rate-limited (429), try next model
            if e.response.status_code in (400, 404, 429):
                continue
            return None
        except httpx.TimeoutException:
            print(f"[LLM Service] Timeout with model: {model}", flush=True)
            continue
        except Exception as e:
            print(f"[LLM Service] Error with model {model}: {e}", flush=True)
            continue

    print("[LLM Service] All Groq models failed.", flush=True)
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
