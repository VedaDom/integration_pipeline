# Overview

Welcome to the Inkomoko Integration Pipeline.

This project is a scalable, observable, and reliable integration between:

- Java/Spring Boot producers (CRM, Inventory)
- Kafka (broker + UI)
- Python async consumer (Analytics pipeline)
- Redis for idempotency

## What’s Implemented

- Producers poll CRM/Inventory and publish to Kafka.
- Consumer merges, dedupes, and delivers to Analytics (JSON or CSV batching).
- DLQ on downstream failures.
- Metrics exported for producers, consumer, and mock APIs.
- Provisioned Grafana dashboard and alerting (configure webhook URL in provisioning to receive alerts).

## Learn More

- [Architecture](architecture.md)
- [Scalability & Throughput validation](scalability.md)
- [Runbook (operations)](runbook.md)
- [Testing & CI](testing.md)
- [Observability](observability.md)

## Submission Notes

- Deliverables included:
  - Java producers (CRM, Inventory) with Dockerfiles and tests
  - Python consumer with tests and metrics
  - Mock APIs, Prometheus, Grafana (dashboard + alerting provisioning)
  - CI workflow for Java/Python tests and coverage artifact uploads
- Helpful links:
  - Source overview: `README.md`
  - CI workflow: `.github/workflows/ci.yml`
  - Load generator: `tools/load_gen.py`
