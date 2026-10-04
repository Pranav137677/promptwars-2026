"""Pytest fixtures for unit and integration testing without external network calls."""


import pytest

from blindspot.app import create_app


@pytest.fixture
def mock_round1_result():
    """Mocked response adhering to Round1AnalysisResponse schema."""
    return {
        "summary": "The student is considering accepting a 6-month software engineering internship offer with ₹25k stipend and full-time hours while completing their final year degree.",
        "what_you_considered": [
            "Financial compensation (stipend covers living expenses)",
            "Commute time (45 minutes each way)",
            "Resume value of software engineering experience"
        ],
        "unstated_assumptions": [
            {
                "assumption": "Assuming the 40-hour work schedule leaves sufficient evening or weekend energy for capstone deliverables.",
                "question_to_test_it": "How many hours per week have past capstone projects required in the final 2 months?"
            },
            {
                "assumption": "Assuming the college will grant attendance waivers or flexible lab hours for an internship.",
                "question_to_test_it": "What is the official written policy on attendance exemptions for off-campus internships?"
            }
        ],
        "overlooked_factors": [
            {
                "factor": "Impact on academic GPA and graduation criteria",
                "category": "Learning and growth",
                "why_it_may_matter": "Falling below attendance thresholds could trigger exam disqualification or delayed graduation."
            },
            {
                "factor": "Quality of mentorship and engineering leadership at the startup",
                "category": "Long-term consequences",
                "why_it_may_matter": "Internship value depends heavily on technical mentorship rather than raw task volume."
            },
            {
                "factor": "Commute fatigue on top of 8-hour work days",
                "category": "Health and wellbeing",
                "why_it_may_matter": "90 minutes of daily round-trip transit adds physical exhaustion before coursework begins."
            }
        ],
        "conflicts_in_reasoning": [
            {
                "tension": "Prioritizing resume enhancement vs. jeopardizing on-time degree completion",
                "explanation": "Accepting the role aims to boost career readiness, yet missing academic attendance requirements directly undermines finishing the degree."
            }
        ],
        "risks_and_unknowns": [
            {
                "item": "Unclear flexibility on overtime hours at a startup",
                "why_it_matters": "Startups often experience sprint crunch weeks that may expand beyond 40 hours."
            },
            {
                "item": "Whether capstone teammates depend on your physical presence on campus",
                "why_it_matters": "Peer collaboration may suffer if you are unreachable during normal college hours."
            }
        ],
        "factor_coverage": [
            {"category": "Finances", "status": "covered"},
            {"category": "Time and schedule", "status": "partly"},
            {"category": "Health and wellbeing", "status": "not_mentioned"},
            {"category": "Relationships", "status": "not_mentioned"},
            {"category": "Learning and growth", "status": "partly"},
            {"category": "Long-term consequences", "status": "not_mentioned"},
            {"category": "Reversibility", "status": "not_mentioned"},
            {"category": "Opportunity cost", "status": "not_mentioned"},
            {"category": "Values and priorities", "status": "covered"}
        ],
        "key_takeaways": [
            "Balancing a 40-hour internship with final-year capstone deliverables poses an unverified schedule conflict.",
            "Career acceleration from early industry experience trades off against the risk of attendance-based graduation delays.",
            "Contingency flexibility remains largely unconfirmed by official written college policies."
        ],
        "probing_questions": [
            "If college administration strictly enforces the 75% attendance rule in month 3, what fallback options exist?",
            "What criteria would clarify whether prioritizing early industry experience or academic coursework serves your long-term goals?",
            "What concrete questions could you ask current interns at this startup regarding realistic workload and mentorship?"
        ],
        "another_perspective": {
            "perspective_favouring_going_ahead": "One perspective favouring going ahead is that practical production experience, a financial stipend, and industry connections can provide an immediate career jumpstart that distinguishes you upon graduation.",
            "perspective_favouring_holding_back": "One perspective favouring holding back is that on-time graduation and protecting your academic standing secure your foundational degree credentials, while new graduate hiring cycles recur regularly."
        }
    }


@pytest.fixture
def mock_round2_result():
    """Mocked response adhering to Round2ReflectionResponse schema."""
    return {
        "what_your_answers_reveal": [
            "Your answers indicate that practical industry exposure is currently prioritized above academic lecture engagement.",
            "You are relying on informal assurances rather than verified written institutional commitments."
        ],
        "tensions_or_contradictions": [
            "You noted that GPA matters for master's applications, yet you plan to allocate minimum effort to academic coursework during this semester."
        ],
        "remaining_blind_spots": [
            "The specific contractual notice period should the workload become unsustainable before final exams.",
            "Contingency plans if your capstone team members request mediator intervention."
        ],
        "reflection_prompts": [
            "What specific threshold of academic strain would signal that the balance is no longer serving your core goals?",
            "How might you secure written confirmation regarding attendance flexibility before signing the internship offer?"
        ]
    }


@pytest.fixture
def app():
    """Flask application test instance."""
    app_instance = create_app({"TESTING": True, "RATELIMIT_ENABLED": True})
    return app_instance


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
