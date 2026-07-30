"""Pydantic data models for structured AI analysis output and internal state.

Defines the complete contract between the LLM, guard layer, and UI. All models
enforce strict validation — malformed LLM output fails loudly rather than rendering
broken UI.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models: Skill Categorization
# ---------------------------------------------------------------------------

class SkillCategory(BaseModel):
    """A categorized group of skills with per-category match/gap tracking."""
    category_name: str = Field(
        ...,
        description="Category label: 'Technical', 'Soft Skills', 'Tools & Platforms', or 'Certifications & Domain'."
    )
    matched: List[str] = Field(
        default_factory=list,
        description="Skills in this category found in both the resume and the JD."
    )
    missing: List[str] = Field(
        default_factory=list,
        description="Skills in this category required by the JD but absent from the resume."
    )


# ---------------------------------------------------------------------------
# Sub-models: Experience Level Assessment
# ---------------------------------------------------------------------------

class ExperienceLevelAssessment(BaseModel):
    """Assessment of seniority alignment between resume signals and JD expectations."""
    resume_level: str = Field(
        ...,
        description="Inferred seniority from resume (e.g., 'Entry-Level', 'Mid-Level', 'Senior')."
    )
    jd_level: str = Field(
        ...,
        description="Expected seniority from JD (e.g., 'Entry-Level', 'Mid-Level', 'Senior')."
    )
    alignment: str = Field(
        ...,
        description="'Aligned', 'Under-Qualified', or 'Over-Qualified'."
    )
    alignment_notes: str = Field(
        default="",
        description="Brief explanation of how the seniority assessment was determined."
    )


# ---------------------------------------------------------------------------
# Sub-models: ATS Warnings
# ---------------------------------------------------------------------------

class ATSWarning(BaseModel):
    """A single ATS compatibility issue detected in the resume content."""
    issue: str = Field(
        ...,
        description="Short description of the formatting or content problem."
    )
    severity: str = Field(
        default="medium",
        description="'low', 'medium', or 'high'."
    )
    recommendation: str = Field(
        default="",
        description="Actionable fix for the issue."
    )


# ---------------------------------------------------------------------------
# Sub-models: Keyword Density
# ---------------------------------------------------------------------------

class KeywordDensityItem(BaseModel):
    """Tracks how often a key JD term appears in the resume."""
    keyword: str = Field(..., description="The keyword or phrase from the JD.")
    jd_count: int = Field(default=1, description="Approximate occurrences in the JD.")
    resume_count: int = Field(default=0, description="Occurrences found in the resume.")


# ---------------------------------------------------------------------------
# Sub-models: Rewrite Suggestions (expanded)
# ---------------------------------------------------------------------------

class RewriteSuggestion(BaseModel):
    """A suggested resume bullet rewrite with grounding verification metadata."""
    original_bullet: Optional[str] = Field(
        default="",
        description="The original bullet or sentence from the resume being reframed/improved."
    )
    suggested_bullet: str = Field(
        ...,
        description="Tailored rewrite of the bullet grounded strictly in existing experience."
    )
    rationale: str = Field(
        ...,
        description="Explanation of why this rewrite aligns better with the target job posting."
    )
    section: str = Field(
        default="Experience",
        description="Which resume section this suggestion targets (Experience, Projects, Education, Summary)."
    )
    # Guard-populated fields (set post-hoc by guard.py, not by LLM)
    flagged_unverifiable: bool = Field(
        default=False,
        description="Flag set by post-hoc guard if suggestion contains terms not found in original resume."
    )
    confidence_score: float = Field(
        default=1.0,
        description="Guard confidence score 0.0–1.0 indicating how well-grounded the suggestion is."
    )
    verification_tier: str = Field(
        default="verified",
        description="'verified', 'partially_verified', or 'unverifiable'."
    )


# ---------------------------------------------------------------------------
# Top-level Result
# ---------------------------------------------------------------------------

class AnalysisResult(BaseModel):
    """Full structured result returned by the LLM analysis pipeline."""

    # --- Flat skill lists (backward compat) ---
    matched_skills: List[str] = Field(
        default_factory=list,
        description="Flat list of skills/keywords found in both the resume and the JD."
    )
    missing_skills: List[str] = Field(
        default_factory=list,
        description="Flat list of key skills/qualifications required by the JD but missing from the resume."
    )

    # --- Categorized skills ---
    skill_categories: List[SkillCategory] = Field(
        default_factory=list,
        description="Skills grouped by category (Technical, Soft Skills, Tools, Certifications)."
    )

    # --- Experience level ---
    experience_assessment: Optional[ExperienceLevelAssessment] = Field(
        default=None,
        description="Seniority alignment analysis between resume and JD."
    )

    # --- Keyword density ---
    keyword_density: List[KeywordDensityItem] = Field(
        default_factory=list,
        description="Top JD keywords with resume occurrence counts."
    )

    # --- ATS warnings ---
    ats_warnings: List[ATSWarning] = Field(
        default_factory=list,
        description="Formatting or content issues that may hinder ATS parsing."
    )

    # --- Rewrite suggestions ---
    rewrite_suggestions: List[RewriteSuggestion] = Field(
        default_factory=list,
        description="3 to 5 concrete bullet rewrite recommendations."
    )

    # --- Readiness tier ---
    readiness_tier: int = Field(
        default=3,
        ge=1, le=5,
        description="Honest 1–5 readiness rating (1=significant gaps, 5=strong match)."
    )
    readiness_rationale: str = Field(
        default="",
        description="Brief justification for the readiness tier assignment."
    )

    # --- Summary ---
    qualitative_summary: str = Field(
        ...,
        description="Honest, evidence-based summary of overall fit without fabricated numeric scores."
    )

    # --- Metadata (set by provider layer, not LLM) ---
    provider_used: Optional[str] = Field(
        default=None,
        description="Name of the AI provider that generated this result (Groq or Gemini)."
    )
