# Risk & Ethics Assessment — ResumeForge-InnoViast

## 1. Ethical Core Philosophy

Resume guidance has direct real-world consequences for job seekers. Providing fabricated claims or false guarantees can cost candidates interviews or damage professional integrity. ResumeForge-InnoViast is built on the principle of **honest advisory boundaries**.

## 2. Risk Matrix & Mitigations

| Risk | Impact | Likelihood | Mitigation Strategy |
|---|---|---|---|
| Model fabricates unheld skills | High | Medium | Strict system prompt rules + `core/guard.py` post-hoc token overlap verification. Unverifiable suggestions are visually flagged in yellow. |
| User over-trusts advisory output | High | Medium | Persistent top banner: "AI-generated advice — verify before use. Not a guarantee of ATS pass-through." |
| PII Exposure / Data Leakage | High | Low | Raw resume and JD text live strictly in session memory (`st.session_state`). SQLite logs persist only metadata (latency, provider, success/failure). |
| Provider Rate Limits / Outages | Medium | Medium | Dual-provider fallback (Groq primary -> Gemini fallback) + Dev Mock Mode for zero-key environments. |

## 3. Human-in-the-Loop Requirement

The application does not perform auto-submits or automated resume rewrites. All outputs are advisory suggestions presented for human evaluation.
