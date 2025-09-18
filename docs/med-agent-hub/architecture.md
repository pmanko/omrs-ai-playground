## System Architecture

High-level
- Router Agent analyzes queries and routes to specialists using ReAct orchestration.
- Medical Agent (MedGemma) answers medical Q&A with clinical disclaimers.
- Clinical Research Agent provides data analytics via MCP tools (Spark, FHIR, literature search).
- Administrative Agent handles appointments via OpenMRS REST API.
- LM Studio provides OpenAI-compatible LLM endpoints for all models.

Message flow
1) Client → Router (JSON-RPC)
2) Router → LLM to analyze
3) Router → Specialist agent
4) Agent → Router with artifacts
5) Router → Client final response

Agent reference
- Router (:9100): orchestration; skills include `route_query` with simple/react modes.
- Medical (:9101): medical info, evidence-based, no diagnosis/prescriptions.
- Clinical (:9102): data analytics via MCP tools - Spark SQL, FHIR search, literature search.
- Administrative (:9103): appointment management via OpenMRS REST API.

A2A implementation
- Agents expose `/.well-known/agent-card.json` for discovery.
- Executors implement business logic; servers host A2A Starlette apps.


