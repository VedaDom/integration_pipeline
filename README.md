# Scalable Integration Pipeline (Kafka + Java Producers + Python Consumers)

This repository implements a polyglot integration pipeline using Java/Spring Boot producers and Python async consumers, with Kafka as the message broker. It includes mock APIs, idempotency via Redis, and observability via Prometheus/Grafana.

## Stack
- Kafka (Bitnami) + Zookeeper
- Kafka UI (Provectus)
- Redis
- Mock APIs (FastAPI)
- Prometheus + Grafana
- Java Producers (Spring Boot): CRM and Inventory
- Python Consumers (async): Analytics pipeline

## Topics
- `customer_data`
- `inventory_data`
- `dlq_customer_data` (dead-letter)
- `dlq_inventory_data` (dead-letter)

## Quick start

Prerequisites: Docker and Docker Compose.

1. Start infrastructure:
   - `docker compose -f infrastructure/docker-compose.yml up -d --build`
2. Access UIs:
   - Kafka UI: http://localhost:8080
   - Grafana: http://localhost:3000 (user: admin / pass: admin)
   - Mock APIs: http://localhost:8000/docs
   - Prometheus: http://localhost:9090
   - Docs (MkDocs Material): http://localhost:8001
3. Explore docs:
   - Overview and architecture live under `docs/` and at the local docs site above.
   - Key pages: Architecture, Scalability, Runbook, Testing, Observability.
3. Create topics (Kafka UI or auto by producers/consumers).
4. Run services:
   - Java producers (see `java-producers/` submodules for instructions)
   - Python consumers (see `python-consumers/` for instructions)

## Delivery modes

- JSON (per-event): consumer posts to `POST /analytics/data`
- CSV (batch): consumer posts to `POST /analytics/upload` with `ANALYTICS_MODE=csv`

## CI

GitHub Actions workflow runs Java and Python tests on push/PR under `.github/workflows/ci.yml`.

### Coverage
- Java (JaCoCo): per-module HTML at `java-producers/<module>/target/jacoco-report/index.html` and XML at `java-producers/<module>/target/site/jacoco/jacoco.xml`.
- Python (pytest-cov): run `pytest --cov=analytics_consumer --cov-report=xml --cov-report=term -q` in `python-consumers/analytics_consumer`; XML at `coverage.xml`.

## Configuration
- All services read config from environment variables with sane defaults; see each submodule README.
- Analytics ingestion can be REST JSON (default) or CSV batch — configurable in the consumer.


## Sample Output

Screenshot of the Grafana dashboard showing producer and consumer metrics during a test run:

![Grafana Dashboard](https://res.cloudinary.com/dlwzb2uh3/image/upload/fl_preserve_transparency/v1757868436/Screenshot_2025-09-14_at_18.34.45_ngla5i.jpg?_s=public-apps)