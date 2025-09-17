# OMRS AI Playground

A healthcare AI research platform showcasing multi-agent architectures (A2A), OpenMRS FHIR integration, and analytics.

## Quick Links

- Med Agent Hub (project docs): `projects/med-agent-hub/docs/docs.md`
- Synthetic Data Uploader: `docs/synthetic-data-uploader/README.md`
- Docs overview: `docs/README.md`

## Components

- Multi-Agent Medical Chat (A2A) — `projects/med-agent-hub/`
- HAPI FHIR datastore — `packages/fhir-datastore-hapi-fhir/`
- Analytics controller & Spark — `packages/analytics-ohs-data-pipes/`

## Development

- Instant OpenHIE v2 packages start via package scripts (see package directories).
- For local A2A development:
  ```bash
  cd projects/med-agent-hub
  cp env.recommended .env
  poetry install
  honcho -f Procfile.dev start
  ```

## License

MIT


