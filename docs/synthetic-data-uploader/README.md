## Synthetic Data Uploader

Purpose
- Upload Synthea-generated FHIR JSON bundles to a target FHIR server (OpenMRS, HAPI, or GCP).

Entrypoint (container)
Env contract:
- `TARGET`: `HAPI` | `OpenMRS` | `GCP`
- `BASE_URL`: FHIR endpoint base (e.g., `http://openmrs:8080/openmrs/ws/fhir2/R4`)
- Optional: `FHIR_USERNAME`, `FHIR_PASSWORD`, `DATASET` (`small`|`full`), `CORES`

Readiness
- Waits for `CapabilityStatement` at `${BASE_URL}/metadata` before upload.

Run (Python)
```bash
cd projects/synthetic-data-uploader/uploader
python -m main OpenMRS http://localhost:8090/openmrs/ws/fhir2/R4 \
  --input_dir ../sample_data_small --convert_to_openmrs
```

Behavior
- For OpenMRS: splits Bundles and uploads Patient → Encounter → Observation, handling identifier conflicts.
- For HAPI/GCP: posts Bundles in an ordered fashion.

Notes
- This tool is standalone; can be packaged into Instant v2 later for one-shot loads.


