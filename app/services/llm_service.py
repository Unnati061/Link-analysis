"""
LLM Service — provider-agnostic wrapper.
Supports Google Gemini, OpenAI, and Anthropic.
"""

import json
import re
from typing import Any

from app.config import settings


class LLMService:
    """
    Sends a prompt to the configured LLM provider and returns a parsed JSON dict.
    """

    def __init__(self):
        self.provider = settings.llm_provider.lower()

    async def generate(self, prompt: str) -> dict[str, Any]:
        """
        Call the LLM and return a parsed Python dict.
        Raises ValueError on failure.
        """
        if self.provider == "gemini":
            return await self._call_gemini(prompt)
        elif self.provider == "openai":
            return await self._call_openai(prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    # ── Gemini ────────────────────────────────────────────────────────────────

    async def _call_gemini(self, prompt: str) -> dict[str, Any]:
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ValueError("google-genai package not installed. Run: pip install google-genai")

        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set in .env")

        client = genai.Client(api_key=settings.gemini_api_key)
        try:
            response = await client.aio.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            if not response.text:
                raise ValueError("Gemini returned an empty response")
            return self._parse_json_response(response.text)
        finally:
            await client.aio.aclose()

    # ── OpenAI ────────────────────────────────────────────────────────────────

    async def _call_openai(self, prompt: str) -> dict[str, Any]:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ValueError("openai package not installed. Run: pip install openai")

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set in .env")

        async with AsyncOpenAI(api_key=settings.openai_api_key) as client:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert business and SEO analyst. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=8192,
            )
        return self._parse_json_response(response.choices[0].message.content)

    # ── Anthropic ─────────────────────────────────────────────────────────────

    async def _call_anthropic(self, prompt: str) -> dict[str, Any]:
        try:
            import anthropic
        except ImportError:
            raise ValueError("anthropic package not installed. Run: pip install anthropic")

        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set in .env")

        async with anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key) as client:
            response = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=8192,
                system="You are an expert business and SEO analyst. Always respond with valid JSON only.",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
        return self._parse_json_response(response.content[0].text)

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json_response(text: str) -> dict[str, Any]:
        """Extract JSON from LLM response (handles markdown code fences)."""
        text = text.strip()
        # Strip ```json ... ``` fences if present
        fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
        if fence_match:
            text = fence_match.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned invalid JSON: {exc}\n\nRaw response:\n{text[:500]}")
