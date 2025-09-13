# Testing

This project includes tests for both Java producers and the Python consumer, and a CI workflow to run them.

## Java (Spring Boot) producers

- Unit tests mock Kafka sends and verify behavior of the publisher:
  - Success path publishes to the main topic.
  - Failure path (send error) publishes to the DLQ topic.
- Files:
  - `java-producers/crm-producer/.../KafkaPublisherTest.java`
  - `java-producers/inventory-producer/.../KafkaPublisherTest.java`
- Run:
  - `cd java-producers && mvn -q -DskipTests=false test`

## Python consumer

- Tests exercise the CSV posting helper and DLQ path using `httpx.MockTransport`:
  - 200 OK -> no DLQ publish
  - 500 error -> DLQ publish with error envelope
- Files:
  - `python-consumers/analytics_consumer/tests/test_post_csv_batch.py`
- Run:
  - `cd python-consumers/analytics_consumer && pip install -r requirements.txt && pytest -q`

## CI

GitHub Actions runs on push/PR:

- File: `.github/workflows/ci.yml`
- Steps:
  - Java: `mvn -q -DskipTests=false test`
  - Python: `pip install -r requirements.txt && pytest -q`
