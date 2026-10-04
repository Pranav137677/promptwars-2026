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


def test_forbidden_words_in_simulated_variations():
    """Verify that multiple synthetically generated responses adhere to non-directive rules."""
    sample_variations = [
        {
            "summary": "The user is balancing career acceleration against academic obligations.",
            "what_you_considered": ["Salary and commute"],
            "unstated_assumptions": [{"assumption": "Attendance is negotiable", "question_to_test_it": "Is it?"}],
            "overlooked_factors": [{"factor": "Exam prep time", "category": "Time and schedule", "why_it_may_matter": "Time crunch"}],
            "conflicts_in_reasoning": [{"tension": "Time balance", "explanation": "Both demand 40h"}],
            "risks_and_unknowns": [{"item": "Project grading", "why_it_matters": "Affects graduation"}],
            "factor_coverage": [{"category": "Time and schedule", "status": "covered"}],
            "probing_questions": ["What is your worst-case academic outcome?"],
            "another_perspective": "One perspective to weigh is postponing internships until after degree completion."
        }
    ]

    for item in sample_variations:
        assert has_directive_language(item) is False
