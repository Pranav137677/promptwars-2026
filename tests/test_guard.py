"""Tests for blindspot.guard verifying detection and redaction of all directive language."""

from blindspot.guard import (
    DEFAULT_NEUTRAL_NOTE,
    find_leading_question_violations,
    find_violations,
    get_all_violations,
    has_directive_language,
    has_leading_question_language,
    redact_directive_language,
    sanitize_text,
)


def test_forbidden_phrases_detected_individually():
    """Verify that every required forbidden phrase is detected."""
    forbidden_samples = [
        "In this situation, you should accept the offer immediately.",
        "Based on your profile, I recommend turning down the internship.",
        "After careful analysis, the best option is clearly option A.",
        "You definitely must go with the startup opportunity.",
        "Under these circumstances, you must focus on your studies.",
        "To maximize learning, it is better to take the internship.",
        "We recommend that you ask for remote flexibility.",
        "My recommendation is to delay the start date.",
        "Taking the job is the right choice for your career.",
        "You ought to decline the position.",
        "Final verdict: proceed with caution.",
        "You need to choose the college project first.",
        "I advise against taking on 40 hours a week.",
        "We advise speaking with your academic advisor."
    ]

    for sample in forbidden_samples:
        violations = find_violations(sample)
        assert len(violations) > 0, f"Failed to detect violation in: '{sample}'"
        assert has_directive_language(sample) is True


def test_case_insensitivity_and_punctuation():
    """Verify case insensitivity and robust matching across punctuation."""
    test_cases = [
        "YOU SHOULD reconsider your timeline.",
        "i recommend taking time to think.",
        "THE BEST OPTION for you is college.",
        "GO WITH your initial instinct!",
        "It Is Better To finish the semester.",
    ]
    for case in test_cases:
        assert has_directive_language(case) is True, f"Failed case: {case}"


def test_clean_reflective_text_passes_untouched():
    """Ensure non-directive, probing, and reflective questions do not trigger false positives."""
    clean_samples = [
        "How might this internship influence your final year GPA?",
        "One perspective to weigh is whether attendance policies are flexible.",
        "What questions could you ask past interns regarding workload?",
        "The stated reasons highlight financial benefit and industry experience.",
        "Should you consider speaking to your college advisor first?",
        "Which factors appear most significant to your long-term goals?",
    ]
    for sample in clean_samples:
        assert find_violations(sample) == []
        assert has_directive_language(sample) is False
        assert sanitize_text(sample) == sample


def test_nested_data_structures():
    """Verify recursive scanning across complex nested dicts and lists."""
    nested_data = {
        "summary": "Neutral summary of the student's dilemma.",
        "assumptions": [
            {"assumption": "Clean assumption", "question": "Clean question"},
            {"assumption": "You should verify this.", "question": "What is the policy?"}
        ],
        "metadata": {
            "notes": {
                "detail": "The best option remains open for discussion."
            }
        }
    }

    assert has_directive_language(nested_data) is True
    violations = get_all_violations(nested_data)
    assert len(violations) >= 2

    cleaned_data, count = redact_directive_language(nested_data)
    assert count == 2
    assert has_directive_language(cleaned_data) is False
    assert DEFAULT_NEUTRAL_NOTE in cleaned_data["assumptions"][1]["assumption"]


def test_sanitize_text_sentence_replacement():
    """Verify that only violating sentences are replaced with the neutral note."""
    text = "The commute is 45 minutes each way. You should accept the offer. There is also college attendance to consider."
    sanitized = sanitize_text(text)
    assert "The commute is 45 minutes each way." in sanitized
    assert "You should accept the offer" not in sanitized
    assert DEFAULT_NEUTRAL_NOTE in sanitized
    assert "There is also college attendance to consider." in sanitized
    assert has_directive_language(sanitized) is False


def test_empty_or_non_string_inputs():
    """Verify graceful handling of non-string and empty inputs."""
    assert find_violations("") == []
    assert find_violations(None) == []  # type: ignore
    assert find_violations(123) == []  # type: ignore
    assert has_directive_language(None) is False
    assert has_directive_language(42) is False
    assert has_directive_language([]) is False
    assert has_directive_language({}) is False


def test_guard_flags_leading_phrasing_in_probing_questions():
    """Verify that guard flags leading, biased, or choice-assuming phrasing in probing questions."""
    leading_questions = [
        "Is accepting the internship really worth the risk to your graduation date?",
        "If you decide to take the offer, how will you manage final exams?",
        "Why take the risk of failing attendance requirements for this stipend?",
        "Wouldn't it be better to wait until after college to start working?",
        "Is it worth sacrificing your GPA for 6 months of experience?",
        "Should you really prioritize short-term cash over your degree?",
    ]

    for question in leading_questions:
        violations = find_leading_question_violations(question)
        assert len(violations) > 0, f"Expected violation for leading question: '{question}'"
        assert has_leading_question_language(question) is True
        assert has_directive_language(question) is True

    # Confirm neutral, balanced questions pass without flagging
    neutral_questions = [
        "What criteria would clarify whether prioritizing early industry experience or academic coursework serves your long-term goals?",
        "What concrete information is known about the team culture and expected daily hours at the startup?",
        "How do the consequences of accepting compare with the consequences of declining across your 2-year timeline?",
        "What specific attendance threshold triggers college disciplinary action according to the written handbook?",
    ]

    for question in neutral_questions:
        assert find_leading_question_violations(question) == []
        assert has_leading_question_language(question) is False

