## Getting Started

Environment
- Copy `projects/med-agent-hub/env.recommended` to `.env` and set `LLM_BASE_URL` (LM Studio) and models.
- Optional: `ORCHESTRATOR_PROVIDER=gemini` with `GEMINI_API_KEY`.
- Optional: Deploy Agenta for web-based prompt management (see Prompt Management below).

Run (development)
```bash
cd projects/med-agent-hub
poetry install
honcho -f Procfile.dev start
```

Endpoints
- Server API: `/:3000` → `/health`, `/generate/{orchestrator|medical|clinical}`, `/chat` (A2A route)
- Agents (dev): Router `:9100`, Medical `:9101`, Clinical `:9102`, Administrative `:9103`

LM Studio Setup
- Start local server (e.g., `http://localhost:1234`), load models for orchestrator/medical/clinical as configured.
- Recommended quantization and GPU options per your hardware.

Configuration Keys
- `LLM_BASE_URL` (required), `ORCHESTRATOR_MODEL`, `MED_MODEL`, `CLINICAL_RESEARCH_MODEL`
- `A2A_ROUTER_URL`, `A2A_MEDGEMMA_URL`, `A2A_CLINICAL_URL` (for native A2A mode)

Prompt Management (Optional)
For web-based prompt editing and testing:
```bash
# Deploy Agenta package
./instant package init -n agenta -d

# Migrate prompts from YAML
cd projects/med-agent-hub
poetry run python -m server.prompt_management.migrate_to_agenta

# Access Agenta UI
open http://localhost:8002
```

See full guide: `projects/med-agent-hub/docs/prompt-management.md`

Troubleshooting
- Connection refused: verify LM Studio and ports.
- Model not found: match model names in LM Studio.
- Agent timeout: raise `CHAT_TIMEOUT_SECONDS`.
- Prompts not loading: check Agenta deployment or set `PROMPT_BACKEND=yaml`.


