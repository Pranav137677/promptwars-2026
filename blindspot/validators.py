"""Input validators and prompt injection defense mechanisms."""

import re
from typing import Any

# Maximum character thresholds
MAX_FIELD_LENGTH = 2000
MAX_TOTAL_LENGTH = 4000
MIN_TEXT_LENGTH = 3

# Basic heuristics for detecting obvious prompt override or injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:(?:previous|prior|above)\s+)?instructions",
    r"disregard\s+(?:all\s+)?(?:(?:previous|prior|above)\s+)?instructions",
    r"forget\s+(?:all\s+)?your\s+instructions",
    r"you\s+are\s+now\s+(?:an?|in)\b",
    r"act\s+as\s+(?:an?|in)\b",
    r"developer\s+mode\b",
    r"jailbreak\b",
    r"system\s+prompt\b",
    r"<\|im_start\|>",
    r"\[system\]",
    r"bypass\s+(?:safety|protocols|guardrails)\b",
    r"override\s+(?:system|safety|core)\s+(?:rules|prompt|instructions)",
    r"pretend\s+to\s+be\b",
]



COMPILED_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS
]


class ValidationError(Exception):
    """Raised when user request payload fails validation checks."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def detect_prompt_injection(text: str) -> bool:
    """Detect whether input text contains evident prompt injection patterns.

    Args:
        text: Input string to inspect.

    Returns:
        True if prompt injection attempt is detected, False otherwise.
    """
    if not isinstance(text, str):
        return False
    return any(p.search(text) for p in COMPILED_INJECTION_PATTERNS)


def sanitize_input_text(text: Any) -> str:
    """Strip whitespace and enforce string conversion safely."""
    if text is None:
        return ""
    if not isinstance(text, str):
        raise ValidationError(
            f"Invalid field type: expected string, got {type(text).__name__}."
        )
    return text.strip()


def validate_round1_input(payload: Any) -> dict[str, str]:
    """Validate and sanitize Round 1 input data.

    Args:
        payload: Decoded JSON dictionary from client.

    Returns:
        Sanitized dictionary containing validated fields.

    Raises:
        ValidationError: If input format, length, or content fails criteria.
    """
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")

    # Validate presence of required keys
    if "decision" not in payload:
        raise ValidationError("Field 'decision' is required.")
    if "reasons" not in payload:
        raise ValidationError("Field 'reasons' is required.")

    decision = sanitize_input_text(payload.get("decision"))
    details = sanitize_input_text(payload.get("details", ""))
    reasons = sanitize_input_text(payload.get("reasons"))
    unsure = sanitize_input_text(payload.get("unsure", ""))

    # Length validations
    if len(decision) < MIN_TEXT_LENGTH:
        raise ValidationError(
            f"Field 'decision' must be at least {MIN_TEXT_LENGTH} characters."
        )
    if len(reasons) < MIN_TEXT_LENGTH:
        raise ValidationError(
            f"Field 'reasons' must be at least {MIN_TEXT_LENGTH} characters."
        )

    for name, val in [
        ("decision", decision),
        ("details", details),
        ("reasons", reasons),
        ("unsure", unsure),
    ]:
        if len(val) > MAX_FIELD_LENGTH:
            raise ValidationError(
                f"Field '{name}' exceeds the maximum allowed length of {MAX_FIELD_LENGTH} characters."
            )

    total_len = len(decision) + len(details) + len(reasons) + len(unsure)
    if total_len > MAX_TOTAL_LENGTH:
        raise ValidationError(
            f"Total input length ({total_len} characters) exceeds the maximum allowed limit of {MAX_TOTAL_LENGTH} characters."
        )

    # Prompt injection check
    for name, val in [
        ("decision", decision),
        ("details", details),
        ("reasons", reasons),
        ("unsure", unsure),
    ]:
        if detect_prompt_injection(val):
            raise ValidationError(
                f"Input field '{name}' contains disallowed instructions. "
                "Please describe only your decision context without command overrides."
            )

    return {
        "decision": decision,
        "details": details,
        "reasons": reasons,
        "unsure": unsure,
    }


def validate_round2_input(payload: Any) -> dict[str, Any]:
    """Validate and sanitize Round 2 input data.

    Args:
        payload: Decoded JSON dictionary from client.

    Returns:
        Sanitized dictionary containing validated fields.

    Raises:
        ValidationError: If input format, length, or content fails criteria.
    """
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object.")

    if "decision" not in payload:
        raise ValidationError("Field 'decision' is required.")
    if "answers" not in payload:
        raise ValidationError("Field 'answers' is required.")

    decision = sanitize_input_text(payload.get("decision"))
    summary = sanitize_input_text(payload.get("summary", ""))

    if len(decision) < MIN_TEXT_LENGTH:
        raise ValidationError(
            f"Field 'decision' must be at least {MIN_TEXT_LENGTH} characters."
        )
    if len(decision) > MAX_FIELD_LENGTH:
        raise ValidationError(
            f"Field 'decision' exceeds maximum length of {MAX_FIELD_LENGTH} characters."
        )

    if detect_prompt_injection(decision) or detect_prompt_injection(summary):
        raise ValidationError(
            "Input contains disallowed instructions. Please provide factual context."
        )

    answers_raw = payload.get("answers")
    if not isinstance(answers_raw, list):
        raise ValidationError("Field 'answers' must be a list of question-answer items.")
    if len(answers_raw) < 1:
        raise ValidationError("At least one answered question is required.")
    if len(answers_raw) > 10:
        raise ValidationError("A maximum of 10 answers can be submitted at once.")

    sanitized_answers: list[dict[str, str]] = []
    total_answers_length = 0

    for idx, item in enumerate(answers_raw):
        if not isinstance(item, dict):
            raise ValidationError(
                f"Answer at index {idx} must be a JSON object with 'question' and 'answer'."
            )
        question = sanitize_input_text(item.get("question", ""))
        answer = sanitize_input_text(item.get("answer", ""))

        if not question:
            raise ValidationError(f"Question at index {idx} cannot be empty.")
        if not answer:
            raise ValidationError(f"Answer for question at index {idx} cannot be empty.")

        if len(question) > 1000:
            raise ValidationError(f"Question at index {idx} exceeds 1000 characters.")
        if len(answer) > MAX_FIELD_LENGTH:
            raise ValidationError(
                f"Answer at index {idx} exceeds {MAX_FIELD_LENGTH} characters."
            )

        if detect_prompt_injection(question) or detect_prompt_injection(answer):
            raise ValidationError(
                f"Answer at index {idx} contains disallowed prompt instructions."
            )

        total_answers_length += len(answer)
        sanitized_answers.append({"question": question, "answer": answer})

    if total_answers_length > MAX_TOTAL_LENGTH:
        raise ValidationError(
            f"Total answers length ({total_answers_length} characters) exceeds limit of {MAX_TOTAL_LENGTH}."
        )

    return {
        "decision": decision,
        "summary": summary,
        "answers": sanitized_answers,
    }
