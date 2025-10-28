<!-- c983a99d-373a-4556-9184-0e97c53e9c98 5c59ae09-0f5c-4194-8ddc-18a881c6f2c5 -->
# Spec Kit Integration for Med-Agent-Hub

## Overview

Establish Spec-Driven Development (SDD) using Spec Kit for the med-agent-hub project, starting with server and web folders. Implement a hybrid workflow that uses structured SDD for features while maintaining direct coding for tests and bug fixes.

## The Hybrid Workflow Model

### Two Development Tracks

**Track A: Spec-Driven Development (Features)**

- New agents, MCP tools, API endpoints, UI components
- Follows: Specify → Plan → Tasks → Implement
- Requires: Human approval at Specify and Plan phases
- Output: Versioned specifications in `.specify/specs/`

**Track B: Direct Coding (Tests & Fixes)**

- Test additions, bug fixes, refactors, docs, dependency updates
- Follows: Code → Test → Commit
- Requires: Clear commit message, links to issues if applicable
- Output: Code changes with conventional commits

**Decision Rule**: "Does this introduce new user-facing behavior or architectural changes?"

- Yes → Track A (SDD)
- No → Track B (Direct)

### Integration Points

1. **Tests for SDD Features**: Test requirements defined in spec, but test code written directly during implementation
2. **Bug Fixes During SDD**: Fix immediately, note in implementation log, no new spec cycle
3. **Spec Updates from Fixes**: If bug reveals spec gap, update spec.md to clarify intent

## Phase 1: Setup and Installation

### 1.1 Add package.json to med-agent-hub

Create `projects/med-agent-hub/package.json`:

```json
{
  "name": "med-agent-hub",
  "version": "0.1.0",
  "private": true,
  "description": "Multi-agent medical chat with SDD workflow",
  "scripts": {
    "spec:init": "spec-kit init",
    "spec:specify": "spec-kit specify",
    "spec:clarify": "spec-kit clarify",
    "spec:plan": "spec-kit plan",
    "spec:tasks": "spec-kit tasks",
    "spec:implement": "spec-kit implement"
  },
  "devDependencies": {
    "spec-kit": "latest"
  }
}
```

Note: The `web/` subdirectory already has its own `package.json` for Svelte. This root-level `package.json` is for development tooling.

### 1.2 Install Spec Kit

```bash
cd projects/med-agent-hub
npm install
```

This installs spec-kit locally to the project, avoiding global installation conflicts.

### 1.3 Initialize Spec Kit

```bash
cd projects/med-agent-hub
npm run spec:init
# or directly: npx spec-kit init --enable-cursor
```

Expected outputs:

- `.specify/` directory created
- `.specify/memory/` for constitution
- `.specify/specs/` for specifications
- `.specify/plans/` for technical plans
- `.specify/tasks/` for task breakdowns

### 1.3 Configure .gitignore

Add to `projects/med-agent-hub/.gitignore`:

```
# Spec Kit working files (keep specs, plans, tasks in version control)
.specify/memory/working/
.specify/cache/
```

Keep committed:

- `.specify/memory/constitution.md`
- `.specify/specs/`
- `.specify/plans/`
- `.specify/tasks/`

## Phase 2: Constitution Creation

### 2.1 Use Cursor Command

In Cursor, execute:

```
/speckit.constitution
```

### 2.2 Constitution Content

Define these sections based on med-agent-hub existing patterns:

**Architecture Principles**

- A2A SDK compliance: All agents use AgentExecutor, TaskUpdater patterns
- MCP tool pattern: All tools extend MCPTool base class
- Dual-source prompts: Support both Agenta API and YAML fallback
- Graceful degradation: External service failures return mock data
- RESTful API: FastAPI with Pydantic models, OpenAPI docs

**Code Quality Standards**

- Python 3.10-3.13 compatibility (per `pyproject.toml`)
- Type hints required for all function signatures
- Black formatter (line-length: 88)
- isort for import organization
- Poetry for dependency management
- Docstrings for all public classes and functions

**Testing Requirements**

- New agent executors: Direct agent tests + integration via router
- MCP tools: `test_mcp_tools_direct.py` + `test_mcp_integration.py` patterns
- API endpoints: Health check + error response tests
- Minimum 70% coverage for new features
- Use pytest fixtures for async tests

**File Organization Standards**

- Agent executors: `server/sdk_agents/{name}_executor.py`
- Agent servers: `server/sdk_agents/{name}_server.py`
- Agent configs: `server/agent_configs/{name}.yaml`
- MCP tools: `server/mcp/{purpose}_tool.py`
- Tests mirror structure: `tests/test_{component}.py`

**Prompt Management**

- All prompts exist in YAML (source of truth)
- Agenta migration script exists for web-based editing
- Load via PromptLoader with automatic fallback
- Template variables documented in YAML comments

**Error Handling Patterns**

```python
# LLM calls: Always use try/except with fallback
try:
    response = await self._call_llm(messages)
except Exception as e:
    logger.error(f"LLM call failed: {e}")
    # Return graceful fallback, never crash

# Task updates: Always update status on errors
except Exception as e:
    await updater.update_status(
        TaskState.failed,
        new_agent_text_message(f"Error: {str(e)}", ...)
    )
```

**Documentation Requirements**

- New agents: Update `docs/architecture/agents.md`
- New MCP tools: Update tool registry and skill documentation
- Configuration changes: Update `env.recommended` and docs
- Breaking changes: Update all affected documentation

## Phase 3: Baseline Documentation

### 3.1 Create Reference Specs (Optional)

Document existing architecture as lightweight reference specs (not for retrofitting, just for clarity):

Create `.specify/specs/reference/`:

- `a2a-architecture.md` - Current A2A agent pattern
- `mcp-tools-pattern.md` - Current MCP tool structure
- `prompt-management.md` - Dual-source loading pattern

These are **read-only references**, not specifications to implement.

### 3.2 Update Development Docs

Create `docs/development/sdd-workflow.md`:

```markdown
# Spec-Driven Development Workflow

## When to Use SDD
- New agent types or executors
- New MCP tools or external integrations
- New API endpoints or request handlers
- New UI components or pages
- Changes to A2A protocol handling

## When to Use Direct Coding
- Adding tests for existing features
- Fixing bugs in documented behavior
- Refactoring without behavior change
- Updating dependencies
- Documentation improvements

## SDD Process
1. /speckit.specify - Define requirements
2. /speckit.clarify - Refine and approve
3. /speckit.plan - Technical architecture
4. /speckit.tasks - Task breakdown
5. /speckit.implement - Execute implementation

## Commit Conventions
- SDD features: `feat: description (spec-001)`
- Bug fixes: `fix: description (#issue)`
- Tests: `test: description`
- Docs: `docs: description`
```

Create `docs/development/spec-kit-quickstart.md`:

- Installation instructions
- Command reference
- Example workflows
- Troubleshooting

## Phase 4: Pilot Feature Implementation

### 4.1 Select Pilot Feature

Choose a small, well-scoped feature to test the workflow:

**Recommended: "Agent Health Monitoring Dashboard"**

- User Story: "As a developer, I want to see health status of all agents in the UI"
- Scope: Server endpoint + web UI component
- Touches both server and web (good for testing cross-component specs)
- Non-critical (safe for learning)

### 4.2 Execute Full SDD Cycle

**Specify Phase**

```
/speckit.specify

"Add a health monitoring dashboard that shows:
- List of all agents (router, medical, clinical, admin)
- Status: online/offline/error
- Response time for last health check
- Model name currently loaded
- Uptime since last restart
- Auto-refresh every 30 seconds"
```

**Clarify Phase**

```
/speckit.clarify
# Refine health check implementation details
# Approve specification
```

**Plan Phase**

```
/speckit.plan
# Technical design:
# - Server: GET /agents/health endpoint
# - Polling: FastAPI + httpx to agent cards
# - Web: Svelte component with setInterval
# - Data model: AgentHealthStatus schema
```

**Tasks Phase**

```
/speckit.tasks
# Auto-generated tasks:
# 1. Create AgentHealthStatus Pydantic model
# 2. Implement /agents/health endpoint
# 3. Add health polling logic
# 4. Create HealthDashboard.svelte component
# 5. Add tests for health endpoint
# 6. Add UI tests for auto-refresh
```

**Implement Phase**

```
/speckit.implement
# AI implements tasks sequentially
# Developer verifies each task
# Tests run after each component
```

### 4.3 Document Pilot Learnings

Create `.specify/lessons/pilot-feature.md`:

- What worked well
- Pain points
- Adjustments to workflow
- Constitution updates needed

## Phase 5: Workflow Enforcement

### 5.1 Pull Request Templates

Create `.github/pull_request_template.md`:

```markdown
## Type of Change
- [ ] Feature (SDD - spec reference: .specify/specs/...)
- [ ] Bug Fix (Direct - issue #...)
- [ ] Test Addition
- [ ] Documentation
- [ ] Refactor

## For Features (SDD Track)
- [ ] Specification approved
- [ ] Plan reviewed
- [ ] Tasks completed
- [ ] Tests passing
- [ ] Documentation updated

## For Bug Fixes (Direct Track)
- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Regression test added
- [ ] Related issue linked
```

### 5.2 Review Checklist

**For SDD Features**:

1. Spec exists and is approved
2. Plan aligns with constitution
3. All tasks marked complete
4. Tests cover requirements
5. Documentation updated

**For Direct Coding**:

1. Change is truly tactical (not a hidden feature)
2. Tests added/updated
3. No architecture changes
4. Clear commit message

## Phase 6: Scaling to Other Projects

### After med-agent-hub Stabilizes

**Expand to Other Packages** (future):

1. Start with application-style packages (similar to med-agent-hub)
2. Infrastructure packages may not need SDD (focus on service definitions)
3. Shared constitution at umbrella level, package-specific amendments

**Not Recommended for SDD** (in umbrella project):

- Pure infrastructure packages (database-postgres, redis)
- Proxy configurations (reverse-proxy-nginx)
- Docker compose orchestration files

## Key Success Factors

### Clear Decision Gate

Before starting any work, ask:

1. "Does this change user-visible behavior?" → YES = SDD likely
2. "Does this change architecture or add components?" → YES = SDD
3. "Is this fixing broken documented behavior?" → YES = Direct coding
4. "Is this adding tests or docs?" → YES = Direct coding

### Disciplined Approval Gates

- **After Specify**: Stakeholder approval required
- **After Plan**: Technical review required
- **Before Implement**: Confirm tasks are complete and ordered

### Continuous Improvement

- Retrospective after each SDD feature
- Update constitution quarterly
- Refine decision gate based on team experience
- Keep documentation current

## Implementation Checklist

### Immediate (Phase 0-1)

- [ ] Install Spec Kit CLI
- [ ] Run `specify init` in med-agent-hub
- [ ] Create constitution via `/speckit.constitution`
- [ ] Document hybrid workflow decision gate
- [ ] Create development guide docs

### Week 1 (Phase 2-3)

- [ ] Team reviews constitution
- [ ] Create reference specs (optional)
- [ ] Update developer documentation
- [ ] Set up PR templates

### Week 2-3 (Phase 4)

- [ ] Select pilot feature
- [ ] Execute full SDD cycle on pilot
- [ ] Team observes workflow
- [ ] Document lessons learned

### Week 4+ (Phase 5-6)

- [ ] Adopt SDD for all new features
- [ ] Monitor adherence via PR reviews
- [ ] Iterate on constitution as needed
- [ ] Plan expansion to other projects

## Appendix: Command Reference

### Spec Kit Commands (in Cursor)

- `/speckit.constitution` - Create/update constitution
- `/speckit.specify` - Define feature requirements
- `/speckit.clarify` - Refine specifications
- `/speckit.plan` - Generate technical plan
- `/speckit.tasks` - Break down into tasks
- `/speckit.implement` - Execute implementation

### Git Workflow

**Branch Naming**:

- Features: `feature/spec-{short-name}`
- Bugs: `fix/{issue-number}-{short-desc}`
- Tests: `test/{component-name}`

**Commit Prefixes**:

- `spec:` - Specification document changes
- `feat:` - Feature implementation (reference spec)
- `fix:` - Bug fixes
- `test:` - Test additions
- `docs:` - Documentation
- `refactor:` - Code refactoring

## Next Steps After Plan Approval

1. Install Spec Kit if not present
2. Run initialization in med-agent-hub
3. Create constitution interactively with team input
4. Document hybrid workflow in development docs
5. Select and execute pilot feature
6. Iterate based on pilot learnings

## Implementation Tasks

The following tasks will be executed after plan approval. Each task is tracked and must be completed before moving to the next phase.

### To-dos

- [ ] example list item.