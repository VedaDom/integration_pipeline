# Scalability & Performance

This section outlines how the pipeline scales to 10,000+ records/hour and to 10+ upstream systems.

## Throughput targets

- 10,000 records/hour (~3 records/sec) is modest for Kafka. Single-partition topics and one consumer instance can handle this comfortably.
- To increase headroom:
  - Increase topic partitions (e.g., 6–12) and run multiple consumer replicas.
  - Enable batching (CSV mode) to reduce downstream POST overhead.
  - Tune producer linger/batch sizes and consumer poll/commit intervals.

## Horizontal scaling

- Producers: add more microservices or modules, each publishing to a topic.
- Topics: partition per key to preserve order and parallelize processing.
- Consumers: scale replicas = partitions for max parallelism.

## Backpressure & resiliency

- Retries with backoff on API calls (producers) and downstream POST (consumer).
- DLQ for downstream failures to prevent blocking the pipeline.
- Idempotency via Redis digest prevents duplicate work and updates.
- Circuit breakers (Resilience4j) recommended for unstable upstreams.

## Multi-system expansion (10+ systems)

- Event-driven integration via Kafka topics per source.
- Contract-first schema evolution (e.g., JSON Schema / Avro if needed).
- Config-driven endpoints and topics for new sources.
- Optionally: use an API gateway for rate-limiting and centralized auth.

## Performance notes

- Use CSV batching for bursty loads; tune `BATCH_MAX_SIZE` and `FLUSH_INTERVAL_SECS`.
- Prefer async HTTP clients (WebClient / httpx) to maximize I/O concurrency.
- Enable gzip on downstream ingestion when payloads get large.

## Throughput validation (10,000/hour)

Use the included load generator to create a steady stream of customers which the CRM producer will fetch and publish to Kafka.

Steps

1. Ensure stack is running:
   - `docker compose -f infrastructure/docker-compose.yml up -d --build`
2. Start load for 10 minutes at 5 customers/sec (~30k/hour potential):
   - `python tools/load_gen.py --base-url http://localhost:8000 --rate 5 --duration 600`
3. Open Grafana (http://localhost:3000) and watch panels:
   - Consumer Msg Rate (should reflect increased traffic)
   - Analytics Success Rate and Latency
   - Mock Analytics Received Rate
   - Producer Records/sec (by topic)
4. Capture screenshots after a few minutes once the rate stabilizes.
5. If needed, adjust `IDEMP_TTL_SECONDS` (consumer) to a low value (e.g., 10s) to permit frequent re-posting during tests.

Notes

- If the CRM producer polls less frequently than the load rate, messages may bunch between polls; increase poll frequency in the producer or extend test duration.
- To test backpressure and DLQ paths, temporarily point `ANALYTICS_URL` to a non-existing endpoint to trigger failures and alerts.
