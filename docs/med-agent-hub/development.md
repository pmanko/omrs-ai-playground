## Development

Local processes
- Use `Procfile.dev` with Honcho to run Router, MedGemma, Clinical, and Web.
- Alternatively, run agents individually via `uvicorn server.sdk_agents.*:app`.

Creating a new agent
1) Agent Card JSON in `server/agent_cards/` (or YAML config in `server/agent_configs/`)
2) Executor in `server/sdk_agents/*_executor.py` (optionally with MCP tool integration)
3) Server in `server/sdk_agents/*_server.py`
4) Register in Router agent registry and `Procfile.dev`

MCP Tool Integration
- Tools in `server/mcp/` follow Model Context Protocol standards
- Tools are stateless functions with JSON Schema validation  
- Executors use `MCPToolRegistry` for tool discovery and invocation
- Tools gracefully degrade to mock data when services unavailable

LLM integration pattern
```python
response = llm_client.generate_chat(
  model=model_name,
  messages=[{"role":"user","content":query}],
  temperature=0.2,
)
```

Testing
- `projects/med-agent-hub/tests/` includes SDK, router, MCP tool, and E2E tests.
- Use `./tests/run_tests.sh` for comprehensive testing including MCP integration.
- Direct MCP tool tests work with mock data (no external services needed).
- Validate agent cards and LLM connectivity before changes.


