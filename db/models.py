"""SQLAlchemy database models for evaluation and telemetry logging."""

import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PromptLog(Base):
    """Logs LLM invocation metadata (no raw resume/JD text stored)."""
    __tablename__ = "prompt_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    prompt_version = Column(String(50), nullable=False)
    provider_used = Column(String(50), nullable=False)
    latency_ms = Column(Integer, nullable=False)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)


class EvaluationResult(Base):
    """Stores results from batch evaluation test suite runs."""
    __tablename__ = "evaluation_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_case_id = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    pass_fail = Column(String(10), nullable=False)  # "pass" or "fail"
    failure_pattern = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class UserFlag(Base):
    """Stores user feedback when an output is flagged as inaccurate in UI."""
    __tablename__ = "user_flag"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    provider_used = Column(String(50), nullable=False)
    user_comment = Column(Text, nullable=True)
