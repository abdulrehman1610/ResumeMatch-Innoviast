"""Prompt builder module for loading templates and constructing structured LLM prompts."""

import os
from pathlib import Path

DEFAULT_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "gap_analysis_v2.txt"
MAX_INPUT_LENGTH = 6000  # Character cap per input section per Rule 14


class PromptBuilderError(Exception):
    """Raised when prompt building fails."""
    pass


def load_prompt_template(template_path: Path = DEFAULT_PROMPT_PATH) -> str:
    """Load a versioned prompt template from disk."""
    if not template_path.exists():
        raise PromptBuilderError(f"Prompt template file not found: {template_path}")
    
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def build_gap_analysis_prompt(
    resume_text: str,
    jd_text: str,
    template_path: Path = DEFAULT_PROMPT_PATH
) -> str:
    """
    Construct the final prompt string from inputs and the gap analysis template.
    Truncates inputs to MAX_INPUT_LENGTH to stay within token/latency limits.
    """
    if not resume_text or not resume_text.strip():
        raise PromptBuilderError("Resume text cannot be empty.")
    if not jd_text or not jd_text.strip():
        raise PromptBuilderError("Job description text cannot be empty.")

    truncated_resume = resume_text.strip()[:MAX_INPUT_LENGTH]
    truncated_jd = jd_text.strip()[:MAX_INPUT_LENGTH]

    template = load_prompt_template(template_path)
    
    formatted_prompt = template.replace(
        "{resume_text}", truncated_resume
    ).replace(
        "{jd_text}", truncated_jd
    )
    return formatted_prompt
