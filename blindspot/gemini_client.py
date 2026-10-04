"""Google Gemini API client using the official google-genai SDK.

Handles strict structured output generation, output guard enforcement,
retries with backoff, and graceful fallback redaction.
"""

import json
import logging
import re
import time
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from blindspot.config import config
from blindspot.guard import (
    has_directive_language,
    redact_directive_language,
)
from blindspot.prompts import (
    STRICT_RETRY_INSTRUCTION,
    SYSTEM_PROMPT_ROUND1,
    SYSTEM_PROMPT_ROUND2,
    build_round1_user_prompt,
    build_round2_user_prompt,
)
from blindspot.schemas import (
    Round1AnalysisResponse,
    Round2ReflectionResponse,
)

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    """Raised when communication with Gemini API fails."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GeminiClient:
    """Wrapper around google-genai Client with retry logic and non-directive output guard."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._api_key = api_key if api_key is not None else config.gemini_api_key
        self._model = model if model is not None else config.gemini_model
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        """Lazily initialize or return the reused genai.Client instance."""
        if self._client is None:
            if not self._api_key:
                raise ValueError(
                    "GEMINI_API_KEY is not configured. Please supply a valid API key."
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        """Clean markdown fences if present and parse JSON."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Failed to decode model JSON: %s. Raw text: %s", e, raw_text)
            raise GeminiServiceError("Model returned malformed JSON output.") from e

    def _call_model(
        self,
        system_instruction: str,
        contents: str,
        response_schema: Any,
        max_output_tokens: int,
    ) -> str:
        """Execute call to Gemini with timeout and a single retry on transient error."""
        client = self._get_client()
        cfg = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
            max_output_tokens=max_output_tokens,
            temperature=0.2,
        )

        models_to_try = [self._model]
        for fallback in ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        last_error: Exception | None = None
        for current_model in models_to_try:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=current_model,
                        contents=contents,
                        config=cfg,
                    )
                    if not response.text:
                        raise GeminiServiceError("Model returned an empty response.")
                    return response.text
                except (APIError, Exception) as e:
                    last_error = e
                    logger.warning(
                        "Gemini API error with %s on attempt %d: %s.",
                        current_model,
                        attempt + 1,
                        e,
                    )
                    if attempt == 0:
                        time.sleep(1.0)
                    else:
                        break  # Move to next model if retry on this model failed

        raise GeminiServiceError(
            f"Failed to communicate with Gemini API after retry: {last_error}"
        )


    def analyze_round1(
        self, decision: str, details: str, reasons: str, unsure: str
    ) -> dict[str, Any]:
        """Perform Round 1 blind spot discovery.

        Runs the Gemini model, checks for directive language violations,
        retries with stricter instructions if needed, and applies neutral redaction
        as a fallback.
        """
        system_prompt = SYSTEM_PROMPT_ROUND1
        user_prompt = build_round1_user_prompt(
            decision=decision, details=details, reasons=reasons, unsure=unsure
        )

        raw_output = self._call_model(
            system_instruction=system_prompt,
            contents=user_prompt,
            response_schema=Round1AnalysisResponse,
            max_output_tokens=2500,
        )

        data = self._extract_json(raw_output)

        # Output Guard: Verify strictly non-directive language
        if has_directive_language(data):
            logger.warning(
                "Directive language detected in Round 1 output. Retrying with stricter instructions..."
            )
            strict_system = f"{system_prompt}\n\n{STRICT_RETRY_INSTRUCTION}"
            retry_output = self._call_model(
                system_instruction=strict_system,
                contents=user_prompt,
                response_schema=Round1AnalysisResponse,
                max_output_tokens=2500,
            )
            data = self._extract_json(retry_output)

            # If still violates after retry, apply neutral redaction
            if has_directive_language(data):
                logger.warning(
                    "Directive language persisted after retry. Applying neutral redaction."
                )
                data, _ = redact_directive_language(data)

        # Validate against schema to ensure complete typing
        validated = Round1AnalysisResponse.model_validate(data)
        return validated.model_dump()

    def reflect_round2(
        self, decision: str, summary: str, answers: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Perform Round 2 reflection analysis on user answers.

        Runs the model, guards against directive language, and ensures no verdicts.
        """
        system_prompt = SYSTEM_PROMPT_ROUND2
        user_prompt = build_round2_user_prompt(
            decision=decision, summary=summary, answers=answers
        )

        raw_output = self._call_model(
            system_instruction=system_prompt,
            contents=user_prompt,
            response_schema=Round2ReflectionResponse,
            max_output_tokens=1500,
        )

        data = self._extract_json(raw_output)

        if has_directive_language(data):
            logger.warning(
                "Directive language detected in Round 2 output. Retrying with stricter instructions..."
            )
            strict_system = f"{system_prompt}\n\n{STRICT_RETRY_INSTRUCTION}"
            retry_output = self._call_model(
                system_instruction=strict_system,
                contents=user_prompt,
                response_schema=Round2ReflectionResponse,
                max_output_tokens=1500,
            )
            data = self._extract_json(retry_output)

            if has_directive_language(data):
                logger.warning(
                    "Directive language persisted in Round 2. Applying neutral redaction."
                )
                data, _ = redact_directive_language(data)

        validated = Round2ReflectionResponse.model_validate(data)
        return validated.model_dump()


# Singleton client instance
gemini_client = GeminiClient()
