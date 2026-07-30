"""Unit tests for hallucination detection guard (v2 with n-gram matching)."""

from core.schema import AnalysisResult, RewriteSuggestion
from core.guard import guard_check, compute_confidence, extract_ngrams, tokenize_clean


def test_tokenize_clean_removes_stop_words():
    """Verify stop words and action verbs are stripped."""
    tokens = tokenize_clean("Developed and deployed machine learning models using Python")
    assert "and" not in tokens
    assert "using" not in tokens
    assert "developed" not in tokens  # action verb
    assert "python" in tokens
    assert "machine" in tokens
    assert "learning" in tokens


def test_extract_bigrams():
    """Verify bigram extraction works correctly."""
    bigrams = extract_ngrams("machine learning models using Python", 2)
    assert "machine learning" in bigrams
    assert "learning models" in bigrams


def test_extract_trigrams():
    """Verify trigram extraction captures 3-word phrases."""
    trigrams = extract_ngrams("natural language processing pipeline", 3)
    assert "natural language processing" in trigrams


def test_compute_confidence_grounded():
    """Verify grounded suggestion gets high confidence."""
    source = "Built machine learning classification models using Python and scikit-learn for sentiment analysis."
    suggested = "Engineered scikit-learn classification models for sentiment analysis tasks."
    confidence, tier = compute_confidence(suggested, source)
    assert confidence >= 0.50
    assert tier in ("verified", "partially_verified")


def test_compute_confidence_hallucinated():
    """Verify net-new invented terms trigger low confidence."""
    source = "Worked on web interface with HTML, CSS, and basic JavaScript."
    suggested = "Architected Kubernetes clusters with Terraform and AWS Lambda serverless functions."
    confidence, tier = compute_confidence(suggested, source)
    assert confidence < 0.30
    assert tier == "unverifiable"


def test_compute_confidence_partial():
    """Verify partially overlapping content gets intermediate tier."""
    source = "Developed REST APIs using Python Flask for data analysis dashboards. Managed SQL database queries and built automated data pipelines."
    suggested = "Engineered Python Flask REST APIs with automated SQL data pipelines for analytics dashboard deployment."
    confidence, tier = compute_confidence(suggested, source)
    # Shares python, flask, rest, apis, sql, data, pipelines, automated, dashboard from source
    # but adds "engineered", "analytics", "deployment" which are new
    assert 0.20 <= confidence <= 0.90
    assert tier in ("partially_verified", "verified")


def test_guard_check_sets_tiers():
    """Verify guard_check populates confidence_score and verification_tier."""
    raw_resume = "Built simple CRUD application using Flask and SQLite for data storage."
    result = AnalysisResult(
        matched_skills=["Python"],
        missing_skills=["Kubernetes"],
        rewrite_suggestions=[
            RewriteSuggestion(
                original_bullet="Built CRUD app.",
                suggested_bullet="Deployed Kubernetes microservices using Docker, Helm, and AWS EC2 for enterprise-scale applications.",
                rationale="Adds cloud infra keywords.",
                section="Experience"
            ),
            RewriteSuggestion(
                original_bullet="Built CRUD app using Flask.",
                suggested_bullet="Developed Flask CRUD application with SQLite database for persistent data storage.",
                rationale="Keeps existing experience, improves specificity.",
                section="Experience"
            )
        ],
        qualitative_summary="Test summary"
    )

    guarded = guard_check(result, raw_resume)

    # First suggestion is hallucinated
    assert guarded.rewrite_suggestions[0].verification_tier == "unverifiable"
    assert guarded.rewrite_suggestions[0].confidence_score < 0.30

    # Second suggestion is grounded
    assert guarded.rewrite_suggestions[1].verification_tier in ("verified", "partially_verified")
    assert guarded.rewrite_suggestions[1].confidence_score > 0.30
