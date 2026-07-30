"""Unit tests for AI Provider fallback orchestration layer (v2)."""

from unittest.mock import patch
import pytest
from core.ai_provider import (
    AIProvider,
    ProviderTimeoutError,
    AIProviderError,
    AllProvidersFailedError
)
from core.schema import AnalysisResult


def test_mock_provider_returns_v2_result():
    """Verify that force_mock mode returns a valid v2 AnalysisResult with all new fields."""
    resume_text = "Python developer with machine learning experience in PyTorch and SQL."
    jd_text = "Entry-level AI Engineer role requiring Python, PyTorch, Docker."

    result = AIProvider.analyze(resume_text, jd_text, force_mock=True)
    assert isinstance(result, AnalysisResult)
    assert len(result.matched_skills) > 0
    assert "Mock" in result.provider_used

    # v2 fields present
    assert len(result.skill_categories) > 0
    assert result.experience_assessment is not None
    assert len(result.keyword_density) > 0
    assert len(result.ats_warnings) > 0
    assert 1 <= result.readiness_tier <= 5
    assert len(result.readiness_rationale) > 0


@patch("core.ai_provider.call_groq")
@patch("core.ai_provider.call_gemini")
def test_groq_failure_triggers_gemini_fallback(mock_gemini, mock_groq):
    """Mandatory test: mocked Groq failure verifies Gemini fallback is called."""
    mock_groq.side_effect = ProviderTimeoutError("Groq call timed out")

    mock_gemini.return_value = {
        "matched_skills": ["Python", "Git"],
        "missing_skills": ["Docker"],
        "rewrite_suggestions": [
            {
                "original_bullet": "Python coding",
                "suggested_bullet": "Developed Python services",
                "rationale": "Clear language",
                "section": "Experience"
            }
        ],
        "qualitative_summary": "Strong core fit.",
        "readiness_tier": 4,
        "readiness_rationale": "Good match"
    }

    resume_text = "Experienced in Python and Git for data processing."
    jd_text = "Need Python engineer with Docker experience."

    result = AIProvider.analyze(resume_text, jd_text)

    mock_groq.assert_called_once()
    mock_gemini.assert_called_once()
    assert result.provider_used == "Gemini"
    assert "Python" in result.matched_skills
    assert result.readiness_tier == 4


@patch("core.ai_provider.call_groq")
@patch("core.ai_provider.call_gemini")
def test_both_providers_fail_raises_exception(mock_gemini, mock_groq):
    """Verify AllProvidersFailedError when both providers fail."""
    mock_groq.side_effect = AIProviderError("Groq 500 server error")
    mock_gemini.side_effect = ProviderTimeoutError("Gemini timed out")

    with pytest.raises(AllProvidersFailedError):
        AIProvider.analyze("Resume text here.", "JD text here.")
