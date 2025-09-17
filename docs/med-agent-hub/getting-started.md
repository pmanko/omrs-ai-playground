## Getting Started

Environment
- Copy `projects/med-agent-hub/env.recommended` to `.env` and set `LLM_BASE_URL` (LM Studio) and models.
- Optional: `ORCHESTRATOR_PROVIDER=gemini` with `GEMINI_API_KEY`.

Run (development)
```bash
cd projects/med-agent-hub
poetry install
honcho -f Procfile.dev start
```

Endpoints
- Server API: `/:3000` → `/health`, `/generate/{orchestrator|medical|clinical}`, `/chat` (A2A route)
- Agents (dev): Router `:9100`, MedGemma `:9101`, Clinical `:9102`

LM Studio Setup
- Start local server (e.g., `http://localhost:1234`), load models for orchestrator/medical/clinical as configured.
- Recommended quantization and GPU options per your hardware.

Configuration Keys
- `LLM_BASE_URL` (required), `ORCHESTRATOR_MODEL`, `MED_MODEL`, `CLINICAL_RESEARCH_MODEL`
- `A2A_ROUTER_URL`, `A2A_MEDGEMMA_URL`, `A2A_CLINICAL_URL` (for native A2A mode)

Troubleshooting
- Connection refused: verify LM Studio and ports.
- Model not found: match model names in LM Studio.
- Agent timeout: raise `CHAT_TIMEOUT_SECONDS`.


