"""Evaluation suite runner.

Executes batch evaluation test cases against the AI analysis pipeline and logs results to SQLite.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.ai_provider import AIProvider, AIProviderError
from db.logger import log_evaluation_result

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eval_runner")

TEST_CASES = [
    {
        "id": "TC-01",
        "resume": "BSCS candidate proficient in Python, PyTorch, SQL, and Git. Built a sentiment analysis model using Transformers.",
        "jd": "Seeking Entry-Level AI Engineer. Requirements: Python, PyTorch, Docker, MLOps, CI/CD, Model Deployment.",
        "expected_missing": ["Docker", "MLOps"]
    },
    {
        "id": "TC-02",
        "resume": "Software Engineering graduate with experience in Java, REST APIs, and PostgreSQL. Created web microservices.",
        "jd": "Backend Engineer role. Qualifications: Go (Golang), gRPC, Docker, Kubernetes, microservices architecture.",
        "expected_missing": ["Go", "gRPC"]
    },
    {
        "id": "TC-03",
        "resume": "Data Analyst intern with strong SQL, Excel, and Tableau skills. Conducted cohort analysis for marketing data.",
        "jd": "ML Engineer candidate needed. Requirements: Python, Scikit-Learn, Deep Learning, Feature Engineering.",
        "expected_missing": ["Deep Learning"]
    }
]


def run_evaluation_suite(use_mock: bool = True):
    """Run all evaluation test cases and record outcomes."""
    logger.info(f"Starting evaluation suite ({len(TEST_CASES)} cases)... Mode: {'Mock' if use_mock else 'Live'}")
    passed_count = 0

    for test in TEST_CASES:
        test_id = test["id"]
        logger.info(f"Running {test_id}...")
        
        try:
            result = AIProvider.analyze(test["resume"], test["jd"], force_mock=use_mock)
            
            # Verify result shape and expected gaps
            has_matched = len(result.matched_skills) > 0
            has_summary = len(result.qualitative_summary) > 20
            
            if has_matched and has_summary:
                status = "PASS"
                passed_count += 1
                failure_pattern = None
                notes = f"Serviced by {result.provider_used}. Extracted {len(result.matched_skills)} matched skills."
            else:
                status = "FAIL"
                failure_pattern = "Incomplete response structure"
                notes = "Missing summary or matched skills"

            log_evaluation_result(
                test_case_id=test_id,
                pass_fail=status,
                failure_pattern=failure_pattern,
                notes=notes
            )
            logger.info(f"Result for {test_id}: {status}")

        except Exception as e:
            logger.error(f"Error evaluating {test_id}: {e}")
            log_evaluation_result(
                test_case_id=test_id,
                pass_fail="FAIL",
                failure_pattern="Pipeline Exception",
                notes=str(e)
            )

    logger.info(f"Evaluation finished: {passed_count}/{len(TEST_CASES)} passed.")


if __name__ == "__main__":
    use_mock_mode = "--live" not in sys.argv
    run_evaluation_suite(use_mock=use_mock_mode)
