# AI Usage & Architecture Documentation — ResumeForge-InnoViast

## 1. Primary & Fallback Models

| Layer | Provider | Model ID | Timeout | Rationale |
|---|---|---|---|---|
| **Primary** | Groq | `llama-3.3-70b-versatile` | 20s | Low latency, open weights, OpenAI-compatible JSON endpoint. |
| **Fallback** | Google Gemini | `gemini-2.0-flash` | 25s | Independent cloud infrastructure, native JSON structured output support. |

## 2. Prompt Evolution & Version Control

- **Version `gap_analysis_v1.txt`**: Defined in `prompts/gap_analysis_v1.txt`.
- Key prompt engineering constraints applied:
  1. Strict JSON output enforcement without conversational wrapper text.
  2. Anti-hallucination constraint prohibiting invented skills or experience.
  3. Grounding requirement forcing every rewrite suggestion to cite actual resume evidence.

## 3. Fallback Trigger Flow

```
User Input -> Prompt Builder
                |
                v
       Try Groq (Primary) ──────(Success)─────> Validated Result
                |
          (Failure / Timeout)
                v
       Try Gemini (Fallback) ───(Success)─────> Validated Result
                |
          (Failure / Timeout)
                v
    AllProvidersFailedError -> Friendly Error State
```

## 4. Known AI Limitations & Guard Mitigations

1. **Token Overlap Guard:** Outputs from both models are post-processed through `core/guard.py`. If key terms in a suggested bullet overlap by <35% with the source resume text, it is tagged as `flagged_unverifiable = True`.
2. **No False Scores:** The application intentionally omits numerical match scores (e.g. "87% match") to prevent over-trust.
