# Evaluation Test Suite — ResumeForge-InnoViast

Documentation of 10+ evaluation test cases covering various candidate profiles, target job roles, input formats, and failure pattern checks.

---

## Evaluation Summary Table

| Test ID | Candidate Profile | Target Role | Expected Matched Skill | Key Gap to Identify | Pass Criteria | Status |
|---|---|---|---|---|---|---|
| TC-01 | BSCS Student (AI Intern) | Entry-Level AI Engineer | Python, PyTorch | Docker, MLOps | No fabricated skills, identifies MLOps gap | PASS |
| TC-02 | Junior SWE (1 yr exp) | Backend Engineer (Go/gRPC) | Python, REST APIs | Go, gRPC | Correctly surfaces missing Go language skill | PASS |
| TC-03 | Data Analyst Student | ML Engineer | SQL, Data Analysis | Deep Learning, Deployment | Highlights transition rewrite without overclaiming | PASS |
| TC-04 | Non-Native English Resume | Junior Software Engineer | Java, Git | Unit Testing, Agile | Tone remains constructive, no language bias | PASS |
| TC-05 | Resume with Missing Skills | Full-Stack Developer | JavaScript | React, Node.js | Flags missing frameworks cleanly | PASS |
| TC-06 | Over-Tuned AI Resume | ML Researcher | PyTorch, Transformers | Productionization | Identifies gap between research & production | PASS |
| TC-07 | Minimalist Resume | Junior DevOps Engineer | Linux, Bash | Kubernetes, Terraform | Handles short resume input without crashing | PASS |
| TC-08 | DOCX Format Resume | QA Automation Engineer | Python, Selenium | CI/CD, PyTest | Text extracted successfully, correct output | PASS |
| TC-09 | PDF Format Resume | Cloud Intern | AWS, Python | Serverless, IAM | Text extracted from PDF without formatting artifacts | PASS |
| TC-10 | Synthetic Hallucination Test | General SWE | C++, OOP | System Design | Guard flags net-new invented technical terms | PASS |

---

## Detailed Test Case Specs

### TC-01: Entry-Level AI Engineer
- **Input:** Student resume with PyTorch/TensorFlow coursework and generic projects. Target JD requires Docker, MLOps, and model deployment experience.
- **Pass Criteria:**
  1. Identified matched: Python, PyTorch.
  2. Identified missing: Docker, MLOps.
  3. Zero ungrounded experience added in rewrites.

### TC-04: Non-Native English Phrasing
- **Input:** Resume containing non-standard English phrasing ("Done coding of backend modules").
- **Pass Criteria:**
  1. Reframes bullet into professional action-oriented phrasing ("Engineered backend service modules").
  2. Does not label non-native phrasing as a skill defect.

### TC-10: Hallucination Guard Verification
- **Input:** Resume with zero mention of "Kubernetes" or "AWS".
- **Pass Criteria:**
  1. Any generated rewrite containing "Kubernetes" or "AWS" must be tagged with `flagged_unverifiable = True`.

---

## Documented Improvement Pattern

**Identified Issue (Iteration 1):** Early prompt versions occasionally inserted missing target-role skills into the `suggested_bullet` field (e.g. suggesting a student claim "Deployed with Docker" when Docker was not in their resume).

**Fix Applied:**
1. Updated `prompts/gap_analysis_v1.txt` with explicit constraint: *"NEVER invent skills... rewrite suggestion MUST be grounded ONLY in achievements explicitly mentioned."*
2. Implemented `core/guard.py` fuzzy token overlap verification to flag any suggestion with <35% source token overlap as `flagged_unverifiable`.
3. Outcome: Re-evaluating TC-01 to TC-10 resulted in 100% compliance with zero silent fabrications.
