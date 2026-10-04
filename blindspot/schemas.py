"""Data schemas and type definitions for requests, responses, and Gemini structured output."""

from typing import Literal

from pydantic import BaseModel, Field

# The 9 mandatory factor categories to evaluate in every decision
MANDATORY_CATEGORIES = [
    "Finances",
    "Time and schedule",
    "Health and wellbeing",
    "Relationships",
    "Learning and growth",
    "Long-term consequences",
    "Reversibility",
    "Opportunity cost",
    "Values and priorities",
]


class Round1Request(BaseModel):
    """Client input payload for Round 1 decision analysis."""

    decision: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The decision the user is considering.",
    )
    details: str = Field(
        default="",
        max_length=2000,
        description="Details and options such as stipend, schedule, location.",
    )
    reasons: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Main reasons why the user is leaning this way.",
    )
    unsure: str = Field(
        default="",
        max_length=2000,
        description="What the user is uncertain or hesitant about.",
    )


class UnstatedAssumption(BaseModel):
    """An unexamined assumption in the user's reasoning with a test question."""

    assumption: str = Field(
        ..., description="The implicit or unexamined assumption made by the user."
    )
    question_to_test_it: str = Field(
        ..., description="An open question that tests whether this assumption holds."
    )


class OverlookedFactor(BaseModel):
    """A crucial factor the user omitted or underweighted."""

    factor: str = Field(..., description="The specific factor overlooked.")
    category: str = Field(
        ...,
        description="One of the core categories (e.g. Finances, Time and schedule, etc.).",
    )
    why_it_may_matter: str = Field(
        ..., description="Neutral explanation of why this factor could affect outcomes."
    )


class ReasoningConflict(BaseModel):
    """An internal tension or contradictory logic within the user's reasoning."""

    tension: str = Field(..., description="The conflicting trade-off or contradiction.")
    explanation: str = Field(
        ...,
        description="Neutral explanation of how these two stated goals or reasons pull in opposite directions.",
    )


class RiskAndUnknown(BaseModel):
    """An identified risk or information gap."""

    item: str = Field(..., description="The risk or missing piece of information.")
    why_it_matters: str = Field(
        ..., description="Why resolving this unknown matters before deciding."
    )


class FactorCoverageItem(BaseModel):
    """Coverage status of each decision dimension."""

    category: str = Field(..., description="Dimension category name.")
    status: Literal["covered", "partly", "not_mentioned"] = Field(
        ...,
        description="Whether the user covered this dimension, partly covered it, or did not mention it.",
    )


class Round1AnalysisResponse(BaseModel):
    """Strict Gemini output schema for Round 1 blind spot discovery."""

    summary: str = Field(
        ...,
        description="Objective restatement of the decision and the user's stated reasons.",
    )
    what_you_considered: list[str] = Field(
        ...,
        description="Factors and aspects the user has already analyzed or articulated well.",
    )
    unstated_assumptions: list[UnstatedAssumption] = Field(
        ..., description="Unstated assumptions and questions to test them."
    )
    overlooked_factors: list[OverlookedFactor] = Field(
        ...,
        description="Overlooked factors categorized across key life/decision dimensions.",
    )
    conflicts_in_reasoning: list[ReasoningConflict] = Field(
        ..., description="Tensions or conflicting priorities in the user's reasoning."
    )
    risks_and_unknowns: list[RiskAndUnknown] = Field(
        ..., description="Risks and missing information gaps."
    )
    factor_coverage: list[FactorCoverageItem] = Field(
        ..., description="Coverage assessment across all 9 evaluation categories."
    )
    probing_questions: list[str] = Field(
        ...,
        description="3 to 6 open-ended probing questions that avoid yes/no answers.",
    )
    another_perspective: str = Field(
        ...,
        description="A thoughtful steelman of an alternative view, framed strictly as 'one perspective to weigh'.",
    )


class QuestionAnswerPair(BaseModel):
    """A probing question answered by the user in Round 2."""

    question: str = Field(..., max_length=1000)
    answer: str = Field(..., min_length=1, max_length=2000)


class Round2Request(BaseModel):
    """Client input payload for Round 2 reflection analysis."""

    decision: str = Field(..., min_length=3, max_length=2000)
    summary: str = Field(default="", max_length=2000)
    answers: list[QuestionAnswerPair] = Field(
        ..., min_length=1, max_length=10
    )


class Round2ReflectionResponse(BaseModel):
    """Strict Gemini output schema for Round 2 user answer reflection."""

    what_your_answers_reveal: list[str] = Field(
        ..., description="Patterns and underlying priorities revealed by the answers."
    )
    tensions_or_contradictions: list[str] = Field(
        ...,
        description="Subtle contradictions or friction emerging from the answers.",
    )
    remaining_blind_spots: list[str] = Field(
        ..., description="Factors that remain unaddressed or unresolved."
    )
    reflection_prompts: list[str] = Field(
        ...,
        description="Final reflective prompts for user self-examination (never advice).",
    )
