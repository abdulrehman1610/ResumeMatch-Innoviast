"""Unit tests for text extraction module."""

import pytest
from core.extraction import (
    extract_resume_text,
    ExtractionError,
    validate_extracted_text
)


def test_validate_extracted_text_valid():
    """Verify that valid text passes validation without error."""
    text = "Word " * 40
    validate_extracted_text(text)  # Should not raise


def test_validate_extracted_text_too_short():
    """Verify that short text raises ExtractionError."""
    text = "Short resume text with few words"
    with pytest.raises(ExtractionError) as exc_info:
        validate_extracted_text(text)
    assert "too short" in str(exc_info.value)


def test_extract_resume_text_unsupported_format():
    """Verify that unsupported file formats raise ExtractionError."""
    file_bytes = b"sample content"
    with pytest.raises(ExtractionError) as exc_info:
        extract_resume_text(file_bytes, "resume.exe")
    assert "Unsupported file extension" in str(exc_info.value)


def test_extract_resume_text_doc_legacy():
    """Verify that legacy .doc files prompt user to convert to docx/pdf."""
    file_bytes = b"sample content"
    with pytest.raises(ExtractionError) as exc_info:
        extract_resume_text(file_bytes, "resume.doc")
    assert "Legacy .doc format is not supported" in str(exc_info.value)


def test_extract_resume_text_txt():
    """Verify plain text extraction."""
    long_text = ("Experienced Software Engineer proficient in Python, SQL, REST APIs, Git, Docker, and AWS. "
                 "Worked on scalable backend systems for e-commerce platforms. " * 3)
    file_bytes = long_text.encode("utf-8")
    extracted = extract_resume_text(file_bytes, "resume.txt")
    assert "Software Engineer" in extracted
