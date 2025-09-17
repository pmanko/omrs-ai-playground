## Development

Local processes
- Use `Procfile.dev` with Honcho to run Router, MedGemma, Clinical, and Web.
- Alternatively, run agents individually via `uvicorn server.sdk_agents.*:app`.

Creating a new agent
1) Agent Card JSON in `server/agent_cards/`
2) Executor in `server/sdk_agents/*_executor.py`
3) Server in `server/sdk_agents/*_server.py`
4) Register in Router agent registry and `Procfile.dev`

LLM integration pattern
```python
response = llm_client.generate_chat(
  model=model_name,
  messages=[{"role":"user","content":query}],
  temperature=0.2,
)
```

Testing
- `projects/med-agent-hub/tests/` includes SDK, router, and E2E tests.
- Validate agent cards and LLM connectivity before changes.


