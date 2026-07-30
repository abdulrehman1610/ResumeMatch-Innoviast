"""Unit tests for prompt builder module."""

import pytest
from core.prompt_builder import build_gap_analysis_prompt, PromptBuilderError


def test_build_gap_analysis_prompt_success():
    """Verify prompt builder correctly injects resume and JD text without KeyError on JSON syntax."""
    resume = "Python developer with machine learning experience."
    jd = "Seeking entry-level AI engineer with Python and Docker skills."
    
    prompt = build_gap_analysis_prompt(resume, jd)
    assert "Python developer" in prompt
    assert "entry-level AI engineer" in prompt
    assert 'matched_skills' in prompt


def test_build_gap_analysis_prompt_empty_inputs():
    """Verify empty inputs raise PromptBuilderError."""
    with pytest.raises(PromptBuilderError):
        build_gap_analysis_prompt("", "Job description text")
    with pytest.raises(PromptBuilderError):
        build_gap_analysis_prompt("Resume text", "")
