"""Output guard enforcing the strict non-directive principle.

Scans all model outputs for forbidden prescriptive phrases, directive recommendations,
or decision verdicts. Provides retry detection and automatic neutral redaction.
"""

import re
from typing import Any

# Forbidden phrasing patterns (case-insensitive word boundaries)
# Per core specification: "The app never recommends, ranks options, gives a verdict,
# or says what to do. Forbidden phrasing includes 'you should', 'I recommend',
# 'the best option', 'go with', 'you must', 'it is better to'."
FORBIDDEN_PATTERNS: list[str] = [
    r"\byou should\b",
    r"\byou must\b",
    r"\byou ought to\b",
    r"\bi recommend\b",
    r"\bwe recommend\b",
    r"\bmy recommendation\b",
    r"\bour recommendation\b",
    r"\bthe best option\b",
    r"\bthe right choice\b",
    r"\bthe best choice\b",
    r"\bgo with\b",
    r"\bit is better to\b",
    r"\byou need to choose\b",
    r"\byou should choose\b",
    r"\bdefinitely choose\b",
    r"\byou definitely should\b",
    r"\bmake sure to pick\b",
    r"\bopt for\b",
    r"\bverdict\b",
    r"\bi advise\b",
    r"\bwe advise\b",
    r"\bmy advice\b",
    r"\bworth the risk\b",
    r"\bif you decide to\b",
    r"\bis it worth\b",
    r"\bwhy take the risk\b",
    r"\bwhy risk\b",
    r"\bwould it be worth\b",
    r"\bis it really worth\b",
    r"\bwouldn't it be better\b",
    r"\bisn't it better\b",
    r"\bshould you really\b",
    r"\bshould you just\b",
]

# Dedicated patterns specifically for flagging leading phrasing in probing questions
LEADING_QUESTION_PATTERNS: list[str] = [
    r"\bworth the risk\b",
    r"\bif you decide to\b",
    r"\bis it worth\b",
    r"\bwhy take the risk\b",
    r"\bwhy risk\b",
    r"\bwould it be worth\b",
    r"\bis it really worth\b",
    r"\bwouldn't it be better\b",
    r"\bisn't it better\b",
    r"\bshould you really\b",
    r"\bshould you just\b",
]

# Compiled regular expressions for fast scanning
COMPILED_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in FORBIDDEN_PATTERNS
]
COMPILED_LEADING_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in LEADING_QUESTION_PATTERNS
]

# Safe neutral fallback replacement note
DEFAULT_NEUTRAL_NOTE: str = (
    "[Reflective note: Consideration highlighted for independent user evaluation.]"
)


def find_leading_question_violations(question: str) -> list[str]:
    """Find leading, biased, or choice-assuming phrasing in a probing question.

    Args:
        question: Probing question text to evaluate.

    Returns:
        List of matched leading phrases.
    """
    if not isinstance(question, str):
        return []
    violations: list[str] = []
    for pattern in COMPILED_LEADING_PATTERNS:
        matches = pattern.findall(question)
        if matches:
            violations.extend(matches)
    return violations


def has_leading_question_language(question: str) -> bool:
    """Return True if probing question contains leading or non-neutral phrasing."""
    return bool(find_leading_question_violations(question))



def find_violations(text: str) -> list[str]:
    """Find all forbidden directive phrases in a given string.

    Args:
        text: The text to examine.

    Returns:
        List of matched forbidden phrases found in the text.
    """
    if not isinstance(text, str):
        return []
    matches: list[str] = []
    for pattern in COMPILED_PATTERNS:
        found = pattern.findall(text)
        if found:
            matches.extend(found)
    return matches


def has_directive_language(data: Any) -> bool:
    """Recursively check whether any string in a dict, list, or primitive contains directive phrasing.

    Args:
        data: Arbitrary data structure (dict, list, str, etc.)

    Returns:
        True if any forbidden directive language is detected, False otherwise.
    """
    if isinstance(data, str):
        return bool(find_violations(data))
    if isinstance(data, dict):
        return any(has_directive_language(v) for v in data.values())
    if isinstance(data, list):
        return any(has_directive_language(item) for item in data)
    return False


def get_all_violations(data: Any) -> list[str]:
    """Recursively collect all forbidden phrases found within data structure.

    Args:
        data: Arbitrary data structure (dict, list, str, etc.)

    Returns:
        List of all matched forbidden phrases (deduplicated preserving order).
    """
    violations: list[str] = []

    def _collect(val: Any) -> None:
        if isinstance(val, str):
            for match in find_violations(val):
                if match.lower() not in [v.lower() for v in violations]:
                    violations.append(match)
        elif isinstance(val, dict):
            for v in val.values():
                _collect(v)
        elif isinstance(val, list):
            for item in val:
                _collect(item)

    _collect(data)
    return violations


def sanitize_text(text: str, fallback_note: str = DEFAULT_NEUTRAL_NOTE) -> str:
    """Replace violating segments or the whole string with neutral phrasing if directive language exists.

    Args:
        text: The string to sanitize.
        fallback_note: The neutral string to substitute.

    Returns:
        Sanitized string containing zero forbidden phrases.
    """
    if not isinstance(text, str):
        return text
    if not find_violations(text):
        return text

    # Split text into sentences and replace offending sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sanitized_parts: list[str] = []
    for s in sentences:
        if find_violations(s):
            sanitized_parts.append(fallback_note)
        else:
            sanitized_parts.append(s)

    result = " ".join(sanitized_parts)
    # Double check that no forbidden phrase slipped through
    if find_violations(result):
        return fallback_note
    return result


def redact_directive_language(
    data: Any, fallback_note: str = DEFAULT_NEUTRAL_NOTE
) -> tuple[Any, int]:
    """Recursively replace any directive phrases in the data structure with a neutral reflection note.

    Args:
        data: Arbitrary data structure (dict, list, str).
        fallback_note: Neutral replacement string.

    Returns:
        Tuple of (sanitized_data, count_of_redactions_made).
    """
    redaction_count = 0

    def _sanitize(item: Any) -> Any:
        nonlocal redaction_count
        if isinstance(item, str):
            if find_violations(item):
                redaction_count += 1
                return sanitize_text(item, fallback_note)
            return item
        if isinstance(item, dict):
            return {k: _sanitize(v) for k, v in item.items()}
        if isinstance(item, list):
            return [_sanitize(v) for v in item]
        return item

    cleaned = _sanitize(data)
    return cleaned, redaction_count
