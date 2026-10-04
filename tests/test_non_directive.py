"""Tests asserting that no model responses contain directive or prescriptive phrasing."""

from blindspot.guard import get_all_violations, has_directive_language
from blindspot.schemas import MANDATORY_CATEGORIES


def test_mock_fixtures_strictly_non_directive(mock_round1_result, mock_round2_result):
    """Assert that default test fixtures and demonstration payloads contain zero directive language."""
    # Round 1 fixture
    assert has_directive_language(mock_round1_result) is False
    violations1 = get_all_violations(mock_round1_result)
    assert violations1 == [], f"Found violations in mock_round1_result: {violations1}"

    # Round 2 fixture
    assert has_directive_language(mock_round2_result) is False
    violations2 = get_all_violations(mock_round2_result)
    assert violations2 == [], f"Found violations in mock_round2_result: {violations2}"


def test_mandatory_categories_coverage(mock_round1_result):
    """Assert that factor coverage checks all 9 mandatory categories."""
    coverage = mock_round1_result.get("factor_coverage", [])
    categories_present = [item["category"] for item in coverage]

    for required_cat in MANDATORY_CATEGORIES:
        assert required_cat in categories_present, f"Missing category: {required_cat}"


def test_key_takeaways_and_dual_perspectives_structure(mock_round1_result):
    """Assert that key takeaways contains 3 bullets and another_perspective provides dual steelmans."""
    takeaways = mock_round1_result.get("key_takeaways", [])
    assert isinstance(takeaways, list)
    assert len(takeaways) == 3, f"Expected 3 key takeaways, got {len(takeaways)}"

    dual_persp = mock_round1_result.get("another_perspective")
    assert isinstance(dual_persp, dict)
    assert "perspective_favouring_going_ahead" in dual_persp
    assert "perspective_favouring_holding_back" in dual_persp
    assert len(dual_persp["perspective_favouring_going_ahead"]) > 20
    assert len(dual_persp["perspective_favouring_holding_back"]) > 20


def test_forbidden_words_in_simulated_variations():
    """Verify that multiple synthetically generated responses adhere to non-directive rules."""
    sample_variations = [
        {
            "summary": "The user is balancing career acceleration against academic obligations.",
            "key_takeaways": [
                "Takeaway bullet 1",
                "Takeaway bullet 2",
                "Takeaway bullet 3"
            ],
            "what_you_considered": ["Salary and commute"],
            "unstated_assumptions": [{"assumption": "Attendance is negotiable", "question_to_test_it": "Is it?"}],
            "overlooked_factors": [{"factor": "Exam prep time", "category": "Time and schedule", "why_it_may_matter": "Time crunch"}],
            "conflicts_in_reasoning": [{"tension": "Time balance", "explanation": "Both demand 40h"}],
            "risks_and_unknowns": [{"item": "Project grading", "why_it_matters": "Affects graduation"}],
            "factor_coverage": [{"category": "Time and schedule", "status": "covered"}],
            "probing_questions": ["What criteria clarify whether to proceed or hold off?"],
            "another_perspective": {
                "perspective_favouring_going_ahead": "One perspective favouring going ahead emphasizes rapid skill acquisition.",
                "perspective_favouring_holding_back": "One perspective favouring holding back emphasizes maintaining academic stability."
            }
        }
    ]

    for item in sample_variations:
        assert has_directive_language(item) is False

