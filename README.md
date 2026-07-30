# 🎯 ResumeMatch

> **Track:** INNOVIAST Track 03 — AI Solutions Engineering  
> **Sprint:** Week 5 — Human-Centered AI Product Innovation  
> **Stack:** Python 3.11+, Streamlit, Groq (Llama 3.3 70B), Google Gemini (2.0 Flash), Pydantic v2, SQLite, PyTest

---

## 📌 Executive Summary

**ResumeMatch** is a single-session Streamlit application built for early-career tech job seekers. It performs a structured, evidence-based gap analysis between a candidate's resume and a specific job posting — returning matched skills, missing qualifications, and grounded bullet rewrite suggestions without inventing unheld skills or presenting vague "match scores".

---

## 🌟 Key Features

1. **Structured Gap Analysis:** Matched skill chips, missing qualification warnings, and actionable bullet rewrite recommendations.
2. **Dual-Provider Fallback Architecture:** Primary calls via **Groq** (`llama-3.3-70b-versatile`); on error or timeout, automatically retries via **Google Gemini** (`gemini-2.0-flash`).
3. **Post-Hoc Hallucination Detection Guard:** Scans AI recommendations against source resume text to tag unverifiable/invented claims in real time.
4. **Honest Advisory Boundary:** Persistent disclaimer banner emphasizing human-in-the-loop verification; zero fabricated match percentages.
5. **Data Privacy First:** Resume text resides strictly in-memory per session. Telemetry logs in SQLite persist execution metadata only.

---

## 🛠️ Project Structure

```
ResumeMatch/
├── app.py                      # Streamlit UI & page flow
├── core/
│   ├── extraction.py           # PDF/DOCX → plain text parser
│   ├── prompt_builder.py       # Template formatting & text cap
│   ├── ai_provider.py          # Groq primary + Gemini fallback orchestration
│   ├── schema.py                # Pydantic v2 output models
│   └── guard.py                 # Hallucination token verification
├── prompts/
│   └── gap_analysis_v1.txt      # Versioned prompt template
├── db/
│   ├── models.py                 # SQLite SQLAlchemy schemas
│   └── logger.py                 # Audit telemetry & feedback logging
├── evaluation/
│   ├── test_cases.md             # 10+ documented test cases
│   └── run_eval.py               # Batch evaluation script
├── docs/
│   ├── PRD.md
│   ├── Architecture.md
│   ├── Design.md
│   ├── Rules.md
│   ├── AI_USAGE.md
│   ├── RISK_ETHICS.md
│   └── PROMPT_LOG.md
├── tests/                      # PyTest automated unit test suite
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
Ensure Python 3.11+ is installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root based on `.env.example`:
```ini
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Note: If API keys are omitted, the application seamlessly runs in Dev Mock Mode for demonstration).*

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```

### 5. Run Unit Tests
```bash
pytest tests/ -v
```

### 6. Run Batch Evaluation Suite
```bash
python evaluation/run_eval.py
```
