"""Post-hoc hallucination and verification guard (v2).

Uses n-gram matching and confidence scoring to detect ungrounded AI suggestions.
Assigns a verification tier (verified / partially_verified / unverifiable) and
a continuous confidence score (0.0–1.0) to each rewrite suggestion.
"""

import re
from typing import List, Set, Tuple
from core.schema import AnalysisResult, RewriteSuggestion

# ---------------------------------------------------------------------------
# Stop words — common English words excluded from comparison
# ---------------------------------------------------------------------------
STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "from", "up", "down", "out", "over", "under",
    "again", "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "s", "t", "can", "will", "just", "don", "should", "now", "i", "me", "my", "myself",
    "we", "our", "ours", "you", "your", "yours", "he", "him", "his", "she", "her",
    "they", "them", "their", "this", "that", "these", "those", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "would", "could", "used", "using", "work", "worked",
    "also", "of", "as", "it", "its", "if", "while", "which", "what", "who"
}

# Common resume action verbs that are generic and shouldn't count as technical evidence
ACTION_VERBS: Set[str] = {
    "developed", "built", "created", "designed", "implemented", "managed",
    "led", "improved", "increased", "reduced", "achieved", "delivered",
    "launched", "engineered", "architected", "established", "maintained",
    "optimized", "streamlined", "collaborated", "mentored", "drove",
    "facilitated", "spearheaded", "executed", "deployed", "integrated",
    "automated", "analyzed", "evaluated", "produced", "leveraged"
}


def tokenize_clean(text: str) -> Set[str]:
    """Extract clean lower-case alphanumeric tokens, excluding stop words and action verbs."""
    words = re.findall(r"\b[a-zA-Z0-9+#\.]{2,}\b", text.lower())
    return {w for w in words if w not in STOP_WORDS and w not in ACTION_VERBS}


def extract_ngrams(text: str, n: int = 2) -> Set[str]:
    """Extract n-grams (default bigrams) from cleaned text for multi-word term matching."""
    words = re.findall(r"\b[a-zA-Z0-9+#\.]{2,}\b", text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    ngrams = set()
    for i in range(len(filtered) - n + 1):
        ngram = " ".join(filtered[i:i + n])
        ngrams.add(ngram)
    return ngrams


def compute_confidence(
    suggested_bullet: str,
    source_resume_text: str
) -> Tuple[float, str]:
    """
    Compute a grounding confidence score (0.0–1.0) and verification tier for a suggestion.

    Uses combined unigram + bigram overlap analysis:
    - Unigram overlap captures individual technical terms
    - Bigram overlap catches multi-word terms like "machine learning", "REST API"

    Tiers:
    - confidence >= 0.60  →  "verified"
    - 0.30 <= confidence < 0.60  →  "partially_verified"
    - confidence < 0.30  →  "unverifiable"
    """
    # Unigram analysis
    suggestion_tokens = tokenize_clean(suggested_bullet)
    source_tokens = tokenize_clean(source_resume_text)

    if not suggestion_tokens:
        return 1.0, "verified"

    unigram_matches = suggestion_tokens.intersection(source_tokens)
    unigram_ratio = len(unigram_matches) / len(suggestion_tokens)

    # Bigram analysis
    suggestion_bigrams = extract_ngrams(suggested_bullet, 2)
    source_bigrams = extract_ngrams(source_resume_text, 2)

    if suggestion_bigrams:
        bigram_matches = suggestion_bigrams.intersection(source_bigrams)
        bigram_ratio = len(bigram_matches) / len(suggestion_bigrams)
    else:
        bigram_ratio = unigram_ratio  # fallback

    # Trigram analysis (bonus signal for longer technical phrases)
    suggestion_trigrams = extract_ngrams(suggested_bullet, 3)
    source_trigrams = extract_ngrams(source_resume_text, 3)

    if suggestion_trigrams:
        trigram_matches = suggestion_trigrams.intersection(source_trigrams)
        trigram_ratio = len(trigram_matches) / len(suggestion_trigrams)
    else:
        trigram_ratio = bigram_ratio

    # Weighted composite score: unigrams 50%, bigrams 35%, trigrams 15%
    confidence = (unigram_ratio * 0.50) + (bigram_ratio * 0.35) + (trigram_ratio * 0.15)
    confidence = round(min(max(confidence, 0.0), 1.0), 3)

    # Assign tier
    if confidence >= 0.60:
        tier = "verified"
    elif confidence >= 0.30:
        tier = "partially_verified"
    else:
        tier = "unverifiable"

    return confidence, tier


def guard_check(result: AnalysisResult, raw_resume_text: str) -> AnalysisResult:
    """
    Scans the AnalysisResult and assigns confidence_score, verification_tier,
    and flagged_unverifiable to each rewrite suggestion based on n-gram grounding
    analysis against the source resume text.
    """
    if not raw_resume_text:
        return result

    updated_suggestions: List[RewriteSuggestion] = []
    for suggestion in result.rewrite_suggestions:
        confidence, tier = compute_confidence(suggestion.suggested_bullet, raw_resume_text)

        updated_suggestion = RewriteSuggestion(
            original_bullet=suggestion.original_bullet,
            suggested_bullet=suggestion.suggested_bullet,
            rationale=suggestion.rationale,
            section=suggestion.section if suggestion.section else "Experience",
            flagged_unverifiable=(tier == "unverifiable"),
            confidence_score=confidence,
            verification_tier=tier
        )
        updated_suggestions.append(updated_suggestion)

    result.rewrite_suggestions = updated_suggestions
    return result
