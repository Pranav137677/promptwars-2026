"""Tests for blindspot.gemini_client with full mocking and zero external network calls."""

import json
from unittest.mock import MagicMock, patch

import pytest

from blindspot.gemini_client import GeminiClient, GeminiServiceError


def test_extract_json_variants():
    """Verify JSON parsing for clean strings and markdown code blocks."""
    client = GeminiClient(api_key="test-key")

    # Plain clean JSON
    plain = '{"key": "value"}'
    assert client._extract_json(plain) == {"key": "value"}

    # Markdown fenced JSON with json tag
    fenced_json = '```json\n{"key": "value"}\n```'
    assert client._extract_json(fenced_json) == {"key": "value"}

    # Markdown fenced JSON without tag
    fenced_plain = '```\n{"key": "value"}\n```'
    assert client._extract_json(fenced_plain) == {"key": "value"}

    # Malformed JSON
    with pytest.raises(GeminiServiceError, match="malformed JSON"):
        client._extract_json("not valid json at all")


def test_missing_api_key_raises_error():
    """Verify initialization or client access fails fast if API key is missing."""
    client = GeminiClient(api_key="")
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
        client._get_client()


def test_analyze_round1_successful_flow(mock_round1_result):
    """Verify successful Round 1 execution when Gemini returns valid structured output."""
    client = GeminiClient(api_key="test-key")

    mock_genai_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_round1_result)
    mock_genai_client.models.generate_content.return_value = mock_response

    client._client = mock_genai_client

    result = client.analyze_round1(
        decision="Internship offer",
        details="Stipend details",
        reasons="Good stipend",
        unsure="Attendance"
    )

    assert result["summary"] == mock_round1_result["summary"]
    assert len(result["factor_coverage"]) == 9
    assert mock_genai_client.models.generate_content.call_count == 1


def test_analyze_round1_directive_language_triggers_retry(mock_round1_result):
    """Verify that directive language in initial response triggers retry with strict prompt."""
    client = GeminiClient(api_key="test-key")

    # First attempt contains forbidden phrasing "you should"
    bad_result = dict(mock_round1_result)
    bad_result["summary"] = "In this situation, you should accept the offer."

    # Second attempt (after retry) is clean
    good_result = dict(mock_round1_result)

    mock_genai_client = MagicMock()
    resp1 = MagicMock()
    resp1.text = json.dumps(bad_result)
    resp2 = MagicMock()
    resp2.text = json.dumps(good_result)

    mock_genai_client.models.generate_content.side_effect = [resp1, resp2]
    client._client = mock_genai_client

    result = client.analyze_round1(
        decision="Internship offer",
        details="Stipend details",
        reasons="Good stipend",
        unsure="Attendance"
    )

    assert mock_genai_client.models.generate_content.call_count == 2
    assert "you should" not in result["summary"]


def test_analyze_round1_persistent_directive_triggers_redaction(mock_round1_result):
    """Verify that if directive language persists after retry, neutral redaction is applied."""
    client = GeminiClient(api_key="test-key")

    # Both attempts contain forbidden phrase "you should"
    bad_result = dict(mock_round1_result)
    bad_result["summary"] = "You should accept the internship immediately."

    mock_genai_client = MagicMock()
    resp1 = MagicMock()
    resp1.text = json.dumps(bad_result)
    resp2 = MagicMock()
    resp2.text = json.dumps(bad_result)

    mock_genai_client.models.generate_content.side_effect = [resp1, resp2]
    client._client = mock_genai_client

    result = client.analyze_round1(
        decision="Internship offer",
        details="Stipend details",
        reasons="Good stipend",
        unsure="Attendance"
    )

    assert mock_genai_client.models.generate_content.call_count == 2
    assert "you should" not in result["summary"].lower()
    assert "Reflective note" in result["summary"]


def test_reflect_round2_successful_flow(mock_round2_result):
    """Verify successful Round 2 reflection analysis."""
    client = GeminiClient(api_key="test-key")

    mock_genai_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_round2_result)
    mock_genai_client.models.generate_content.return_value = mock_response

    client._client = mock_genai_client

    result = client.reflect_round2(
        decision="Internship decision",
        summary="Neutral summary",
        answers=[{"question": "Q1", "answer": "A1"}]
    )

    assert len(result["what_your_answers_reveal"]) == 2
    assert len(result["reflection_prompts"]) == 2


def test_reflect_round2_directive_retry_and_redaction(mock_round2_result):
    """Verify that directive language in Round 2 triggers retry and neutral redaction."""
    client = GeminiClient(api_key="test-key")

    bad_resp = dict(mock_round2_result)
    bad_resp["what_your_answers_reveal"] = ["You should definitely make this choice."]

    mock_genai_client = MagicMock()
    resp1 = MagicMock()
    resp1.text = json.dumps(bad_resp)
    resp2 = MagicMock()
    resp2.text = json.dumps(bad_resp)  # Still bad on retry

    mock_genai_client.models.generate_content.side_effect = [resp1, resp2]
    client._client = mock_genai_client

    result = client.reflect_round2(
        decision="Internship decision",
        summary="Summary",
        answers=[{"question": "Q1", "answer": "A1"}]
    )

    assert mock_genai_client.models.generate_content.call_count == 2
    assert "you should" not in result["what_your_answers_reveal"][0].lower()
    assert "Reflective note" in result["what_your_answers_reveal"][0]


def test_call_model_empty_response():
    """Verify error raised when model produces empty text."""
    client = GeminiClient(api_key="test-key")
    mock_genai_client = MagicMock()
    empty_resp = MagicMock()
    empty_resp.text = ""
    mock_genai_client.models.generate_content.return_value = empty_resp
    client._client = mock_genai_client

    with patch("time.sleep", return_value=None):
        with pytest.raises(GeminiServiceError, match="Failed to communicate with Gemini API"):
            client.analyze_round1("Decision", "", "Reasons", "")


def test_gemini_error_retry_and_failure():
    """Verify retry logic on transient Gemini error and eventual exception handling."""
    client = GeminiClient(api_key="test-key")
    mock_genai_client = MagicMock()

    # Create dummy API error
    mock_genai_client.models.generate_content.side_effect = Exception("Connection timeout")
    client._client = mock_genai_client

    with patch("time.sleep", return_value=None):
        with pytest.raises(GeminiServiceError, match="Failed to communicate with Gemini API"):
            client.analyze_round1("Decision", "", "Reasons", "")

    # Assert 2 attempts were made
    assert mock_genai_client.models.generate_content.call_count == 2

