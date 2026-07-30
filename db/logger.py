"""Database logging and telemetry interface."""

import os
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, PromptLog, EvaluationResult, UserFlag

DB_PATH = Path(__file__).parent.parent / "resumematch.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Ensure database tables exist."""
    Base.metadata.create_all(bind=engine)


# Initialize DB automatically on import
init_db()


def log_prompt_call(
    prompt_version: str,
    provider_used: str,
    latency_ms: int,
    success: bool = True,
    error_message: Optional[str] = None
) -> None:
    """Log LLM call metadata to SQLite without persisting user content."""
    session = SessionLocal()
    try:
        entry = PromptLog(
            prompt_version=prompt_version,
            provider_used=provider_used,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message
        )
        session.add(entry)
        session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()


def log_evaluation_result(
    test_case_id: str,
    pass_fail: str,
    failure_pattern: Optional[str] = None,
    notes: Optional[str] = None
) -> None:
    """Log evaluation run outcome."""
    session = SessionLocal()
    try:
        entry = EvaluationResult(
            test_case_id=test_case_id,
            pass_fail=pass_fail,
            failure_pattern=failure_pattern,
            notes=notes
        )
        session.add(entry)
        session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()


def log_user_flag(
    provider_used: str,
    user_comment: Optional[str] = None
) -> None:
    """Log user feedback flagging an output as inaccurate."""
    session = SessionLocal()
    try:
        entry = UserFlag(
            provider_used=provider_used,
            user_comment=user_comment
        )
        session.add(entry)
        session.commit()
    except Exception as e:
        session.rollback()
    finally:
        session.close()
