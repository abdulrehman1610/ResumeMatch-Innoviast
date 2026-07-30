"""Unit tests for Pydantic schema validation (v2 expanded)."""

import pytest
from pydantic import ValidationError
from core.schema import (
    AnalysisResult, RewriteSuggestion, SkillCategory,
    ExperienceLevelAssessment, ATSWarning, KeywordDensityItem
)


def test_valid_full_analysis_result():
    """Verify that a complete v2 result parses into AnalysisResult."""
    data = {
        "matched_skills": ["Python", "Git"],
        "missing_skills": ["Docker"],
        "skill_categories": [
            {"category_name": "Technical", "matched": ["Python"], "missing": ["Docker"]}
        ],
        "experience_assessment": {
            "resume_level": "Entry-Level",
            "jd_level": "Mid-Level",
            "alignment": "Under-Qualified",
            "alignment_notes": "1 year vs 3+ expected"
        },
        "keyword_density": [
            {"keyword": "Python", "jd_count": 3, "resume_count": 5}
        ],
        "ats_warnings": [
            {"issue": "No Skills section", "severity": "high", "recommendation": "Add one"}
        ],
        "rewrite_suggestions": [
            {
                "original_bullet": "Did coding",
                "suggested_bullet": "Developed backend APIs using Python",
                "rationale": "More descriptive",
                "section": "Experience"
            }
        ],
        "readiness_tier": 3,
        "readiness_rationale": "Moderate match",
        "qualitative_summary": "Good overall fit with some gaps."
    }
    result = AnalysisResult(**data)
    assert result.readiness_tier == 3
    assert len(result.skill_categories) == 1
    assert result.experience_assessment.alignment == "Under-Qualified"
    assert len(result.keyword_density) == 1
    assert len(result.ats_warnings) == 1
    assert result.rewrite_suggestions[0].section == "Experience"


def test_minimal_analysis_result():
    """Verify backward compat — only required fields."""
    data = {
        "matched_skills": ["Python"],
        "qualitative_summary": "Decent fit."
    }
    result = AnalysisResult(**data)
    assert result.readiness_tier == 3  # default
    assert result.skill_categories == []
    assert result.experience_assessment is None


def test_invalid_readiness_tier_out_of_range():
    """Verify tier must be 1-5."""
    data = {
        "matched_skills": [],
        "qualitative_summary": "Test",
        "readiness_tier": 7
    }
    with pytest.raises(ValidationError):
        AnalysisResult(**data)


def test_missing_required_summary():
    """Verify that missing qualitative_summary raises ValidationError."""
    data = {"matched_skills": ["Python"]}
    with pytest.raises(ValidationError):
        AnalysisResult(**data)


def test_rewrite_suggestion_defaults():
    """Verify that RewriteSuggestion has correct defaults for guard fields."""
    s = RewriteSuggestion(suggested_bullet="Test", rationale="Reason")
    assert s.flagged_unverifiable is False
    assert s.confidence_score == 1.0
    assert s.verification_tier == "verified"
    assert s.section == "Experience"
