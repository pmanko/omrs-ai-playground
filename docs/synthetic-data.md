## Synthetic data uploader and generator

Images
- Uploader (`SYNTHEA_UPLOADER_IMAGE`): runs vendored `synthea-hiv/uploader/main.py` against a FHIR endpoint and exits.
- Generator (`SYNTHEA_GENERATOR_IMAGE`): wraps `generator/Dockerfile` to produce datasets in future.

Uploader env
- TARGET: HAPI | OPENMRS
- BASE_URL: FHIR base URL (e.g., http://hapi-fhir:8080/fhir or http://openmrs:8080/openmrs/ws/fhir2/R4)
- FHIR_USERNAME, FHIR_PASSWORD (optional)
- DATASET: small | full (small maps to vendored sample_data)
- CORES: default 4

Lifecycle wiring
- OpenMRS init: runs a one-shot loader with DATASET=small, then removes it.
- HAPI init: runs a one-shot loader with DATASET=full, then removes it.

Build
- Set `SYNTHEA_UPLOADER_IMAGE` and `SYNTHEA_GENERATOR_IMAGE` in package metadata or root .env.
- Build: `./build-custom-images.sh synthetic-data-uploader`

References
- OHS tutorial (test servers/uploader): https://google.github.io/fhir-data-pipes/tutorials/test_servers/
- Upstream synthea-hiv: https://github.com/google/fhir-data-pipes/tree/master/synthea-hiv

