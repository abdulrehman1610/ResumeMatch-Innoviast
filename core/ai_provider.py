"""AI Provider Orchestration Layer (v2).

Handles dual-provider execution (Groq primary -> Gemini fallback) with strict
Pydantic output validation and post-hoc hallucination guarding. Uses the v2
prompt template for multi-dimensional professional analysis.
"""

import os
import json
import logging
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from core.schema import (
    AnalysisResult, RewriteSuggestion, SkillCategory,
    ExperienceLevelAssessment, ATSWarning, KeywordDensityItem
)
from core.prompt_builder import build_gap_analysis_prompt
from core.guard import guard_check

load_dotenv()

logger = logging.getLogger(__name__)

# Constants
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GROQ_TIMEOUT_SECONDS = 20
GEMINI_TIMEOUT_SECONDS = 25


class AIProviderError(Exception):
    """Base exception for AI Provider errors."""
    pass


class ProviderTimeoutError(AIProviderError):
    """Raised when a provider call times out."""
    pass


class ProviderAuthError(AIProviderError):
    """Raised when provider authentication fails."""
    pass


class AllProvidersFailedError(AIProviderError):
    """Raised when both primary (Groq) and fallback (Gemini) providers fail."""
    pass


def parse_json_response(raw_text: str) -> Dict[str, Any]:
    """Clean markdown code block wrappers if present and parse JSON."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON output: {e}. Raw text: {raw_text[:200]}")
        raise AIProviderError(f"LLM returned invalid JSON output: {str(e)}")


def call_groq(prompt: str) -> Dict[str, Any]:
    """Call Groq primary provider and return parsed JSON dict."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        raise ProviderAuthError("GROQ_API_KEY is not configured.")

    try:
        from groq import Groq
        client = Groq(api_key=api_key, timeout=GROQ_TIMEOUT_SECONDS)

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional ATS resume analyst. Return ONLY valid JSON matching the requested schema exactly."},
                {"role": "user", "content": prompt}
            ],
            model=GROQ_MODEL,
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            raise AIProviderError("Groq returned an empty response.")
        return parse_json_response(content)
    except (ProviderAuthError, AIProviderError):
        raise
    except Exception as e:
        err_msg = str(e)
        if "auth" in err_msg.lower() or "api key" in err_msg.lower() or "401" in err_msg:
            raise ProviderAuthError(f"Groq auth error: {err_msg}")
        elif "timeout" in err_msg.lower():
            raise ProviderTimeoutError(f"Groq request timed out: {err_msg}")
        else:
            raise AIProviderError(f"Groq call failed: {err_msg}")


def call_gemini(prompt: str) -> Dict[str, Any]:
    """Call Google Gemini fallback provider and return parsed JSON dict."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ProviderAuthError("GEMINI_API_KEY is not configured.")

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={"response_mime_type": "application/json", "temperature": 0.2}
        )
        response = model.generate_content(prompt)
        if not response.text:
            raise AIProviderError("Gemini returned an empty response.")
        return parse_json_response(response.text)
    except (ProviderAuthError, AIProviderError):
        raise
    except Exception as e:
        err_msg = str(e)
        if "auth" in err_msg.lower() or "api_key" in err_msg.lower() or "400" in err_msg:
            raise ProviderAuthError(f"Gemini auth error: {err_msg}")
        elif "timeout" in err_msg.lower():
            raise ProviderTimeoutError(f"Gemini request timed out: {err_msg}")
        else:
            raise AIProviderError(f"Gemini call failed: {err_msg}")


def generate_mock_result(resume_text: str, jd_text: str) -> AnalysisResult:
    """Generate a comprehensive mock AnalysisResult for dev/demo testing."""
    return AnalysisResult(
        matched_skills=["Python", "Machine Learning", "Git", "REST APIs", "SQL", "Data Analysis"],
        missing_skills=["Docker", "Kubernetes", "AWS", "CI/CD Pipeline", "System Design"],
        skill_categories=[
            SkillCategory(
                category_name="Technical",
                matched=["Python", "Machine Learning", "SQL", "Data Analysis"],
                missing=["Docker", "Kubernetes", "System Design"]
            ),
            SkillCategory(
                category_name="Soft Skills",
                matched=["Problem Solving", "Team Collaboration"],
                missing=["Technical Leadership", "Mentoring"]
            ),
            SkillCategory(
                category_name="Tools & Platforms",
                matched=["Git", "VS Code", "Jupyter"],
                missing=["AWS", "Docker Compose", "Jenkins"]
            ),
            SkillCategory(
                category_name="Certifications & Domain",
                matched=[],
                missing=["AWS Cloud Practitioner", "TensorFlow Certification"]
            )
        ],
        experience_assessment=ExperienceLevelAssessment(
            resume_level="Entry-Level",
            jd_level="Mid-Level",
            alignment="Under-Qualified",
            alignment_notes="Resume shows ~1 year of internship experience across 2 roles; JD expects 2–4 years of professional experience with production system ownership."
        ),
        keyword_density=[
            KeywordDensityItem(keyword="machine learning", jd_count=4, resume_count=2),
            KeywordDensityItem(keyword="Python", jd_count=3, resume_count=5),
            KeywordDensityItem(keyword="Docker", jd_count=3, resume_count=0),
            KeywordDensityItem(keyword="AWS", jd_count=4, resume_count=0),
            KeywordDensityItem(keyword="REST API", jd_count=2, resume_count=1),
            KeywordDensityItem(keyword="CI/CD", jd_count=2, resume_count=0),
            KeywordDensityItem(keyword="data pipeline", jd_count=2, resume_count=1),
            KeywordDensityItem(keyword="agile", jd_count=2, resume_count=0),
        ],
        ats_warnings=[
            ATSWarning(
                issue="No dedicated 'Technical Skills' section heading detected",
                severity="high",
                recommendation="Add a clearly labeled 'Technical Skills' section near the top listing key technologies."
            ),
            ATSWarning(
                issue="Resume may lack quantified achievements in bullet points",
                severity="medium",
                recommendation="Add metrics (percentages, counts, timeframes) to at least 3 experience bullets."
            ),
            ATSWarning(
                issue="Education section appears after experience — may be expected first for entry-level",
                severity="low",
                recommendation="For entry-level roles, consider placing Education before Experience."
            ),
        ],
        rewrite_suggestions=[
            RewriteSuggestion(
                original_bullet="Worked on AI models and data analysis.",
                suggested_bullet="Developed and evaluated supervised ML models using scikit-learn and PyTorch, increasing classification accuracy by 14% on a 50K-record dataset.",
                rationale="Quantifies achievement, names specific frameworks from the JD, and demonstrates scale.",
                section="Experience"
            ),
            RewriteSuggestion(
                original_bullet="Built web applications using Python.",
                suggested_bullet="Engineered high-throughput REST APIs using Python and Flask, serving real-time model inference endpoints handling 200+ requests/minute.",
                rationale="Highlights API design, deployment vocabulary, and throughput metrics aligned with the target role.",
                section="Experience"
            ),
            RewriteSuggestion(
                original_bullet="Participated in team projects.",
                suggested_bullet="Collaborated in a 4-person agile team to deliver an end-to-end data pipeline processing 10GB daily, using Git for version control and Jira for sprint tracking.",
                rationale="Transforms a vague statement into a structured achievement with team size, methodology, and tool specifics.",
                section="Projects"
            ),
        ],
        readiness_tier=3,
        readiness_rationale="Candidate demonstrates strong Python and ML fundamentals covering ~55% of core technical requirements. The primary gap is cloud infrastructure and containerization experience (Docker/AWS), which represents 3 of the top 5 JD priorities.",
        qualitative_summary="The candidate shows solid foundational skills in Python, Machine Learning, and data analysis that align with the role's core technical needs. The most critical gap is the absence of cloud deployment and containerization experience (Docker, AWS), which the JD emphasizes heavily. The strongest selling point is hands-on ML project experience with quantifiable outcomes. As an immediate next step, completing a personal project that deploys an ML model via Docker on AWS would directly address the top two gaps.",
        provider_used="Mock Provider (Dev Mode)"
    )


class AIProvider:
    """Public interface for executing resume-JD gap analysis."""

    @staticmethod
    def analyze(resume_text: str, jd_text: str, force_mock: bool = False) -> AnalysisResult:
        """
        Executes end-to-end gap analysis with automatic primary -> fallback retry.

        Pipeline:
        1. Build v2 prompt from template.
        2. Attempt primary call via Groq.
        3. On failure, log warning and attempt fallback via Gemini.
        4. Validate returned dict against AnalysisResult Pydantic schema.
        5. Run post-hoc hallucination guard check.
        6. Return validated AnalysisResult.
        """
        if force_mock:
            logger.info("Executing analysis via Mock Provider (forced).")
            return guard_check(generate_mock_result(resume_text, jd_text), resume_text)

        # Use v2 prompt template
        from pathlib import Path
        v2_template = Path(__file__).parent.parent / "prompts" / "gap_analysis_v2.txt"
        prompt = build_gap_analysis_prompt(resume_text, jd_text, template_path=v2_template)

        result_dict: Optional[Dict[str, Any]] = None
        provider_name: str = ""

        # Step 1: Try Primary Provider (Groq)
        try:
            logger.info("Attempting analysis via Groq primary provider...")
            result_dict = call_groq(prompt)
            provider_name = "Groq"
        except (AIProviderError, ProviderAuthError, ProviderTimeoutError) as groq_err:
            logger.warning(f"Groq primary provider failed ({groq_err}). Retrying via Gemini fallback...")

            # Step 2: Try Fallback Provider (Gemini)
            try:
                result_dict = call_gemini(prompt)
                provider_name = "Gemini"
            except (AIProviderError, ProviderAuthError, ProviderTimeoutError) as gemini_err:
                logger.error(f"Gemini fallback provider also failed ({gemini_err}).")

                # Dev fallback if no keys configured
                if isinstance(groq_err, ProviderAuthError) and isinstance(gemini_err, ProviderAuthError):
                    logger.info("No valid API keys detected. Falling back to Dev Mock Mode.")
                    return guard_check(generate_mock_result(resume_text, jd_text), resume_text)

                raise AllProvidersFailedError(
                    f"Both Groq and Gemini providers failed. Groq: {groq_err}. Gemini: {gemini_err}."
                )

        # Step 3: Validate against Pydantic schema
        try:
            parsed_result = AnalysisResult(**result_dict)
            parsed_result.provider_used = provider_name
        except Exception as validation_err:
            logger.error(f"Pydantic validation failed for provider {provider_name}: {validation_err}")
            raise AIProviderError(f"Model output failed schema validation: {validation_err}")

        # Step 4: Run post-hoc guard check
        guarded_result = guard_check(parsed_result, resume_text)
        return guarded_result
