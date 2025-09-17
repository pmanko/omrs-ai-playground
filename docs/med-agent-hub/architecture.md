## System Architecture

High-level
- Router Agent analyzes queries and routes to specialists.
- MedGemma Agent answers medical Q&A with disclaimers.
- Clinical Research Agent provides research/statistical insights.
- LM Studio provides OpenAI-compatible LLM endpoints.

Message flow
1) Client → Router (JSON-RPC)
2) Router → LLM to analyze
3) Router → Specialist agent
4) Agent → Router with artifacts
5) Router → Client final response

Agent reference
- Router (:9100): orchestration; skills include `route_query` with simple/react modes.
- MedGemma (:9101): medical info, evidence-based, no diagnosis/prescriptions.
- Clinical (:9102): research queries, statistics, literature/guidelines.

A2A implementation
- Agents expose `/.well-known/agent-card.json` for discovery.
- Executors implement business logic; servers host A2A Starlette apps.


