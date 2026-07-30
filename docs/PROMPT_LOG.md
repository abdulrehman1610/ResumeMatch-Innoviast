# Prompt Audit & Log — ResumeForge-InnoViast

## Prompt Version History

### Version: `gap_analysis_v1`
- **File:** `prompts/gap_analysis_v1.txt`
- **Date Created:** Week 5, Day 1
- **Target Providers:** Groq (`llama-3.3-70b-versatile`), Google Gemini (`gemini-2.0-flash`)
- **JSON Schema:**
```json
{
  "matched_skills": ["string"],
  "missing_skills": ["string"],
  "rewrite_suggestions": [
    {
      "original_bullet": "string",
      "suggested_bullet": "string",
      "rationale": "string"
    }
  ],
  "qualitative_summary": "string"
}
```
- **Changes / Iteration Notes:** Added explicit anti-hallucination instruction: *"NEVER invent skills... rewrite suggestion MUST be grounded ONLY in achievements explicitly mentioned."*
