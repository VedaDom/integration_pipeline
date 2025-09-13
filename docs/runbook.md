# Runbook

## Start the stack

- `docker compose -f infrastructure/docker-compose.yml up -d --build`

## Service URLs

- Kafka UI: http://localhost:8080
- Mock APIs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Docs: http://localhost:8001

## Common checks

- Prometheus targets: http://localhost:9090/targets
- Grafana dashboard: "Kafka Integration Overview"
- Kafka topics: `customer_data`, `inventory_data`, `analytics_dlq`

## Logs

- Follow consumer & mock APIs:
  - `docker compose -f infrastructure/docker-compose.yml logs -f python-consumer mock-apis`
- Producers:
  - `docker compose -f infrastructure/docker-compose.yml logs -f crm-producer inventory-producer`

## Dedup cache (Redis)

- Clear dedup keys:
  - `docker exec -it infrastructure-redis-1 redis-cli FLUSHALL`
- Tune dedup TTL:
  - `IDEMP_TTL_SECONDS` in `docker-compose.yml` under `python-consumer`.

## Switching Analytics delivery mode

- JSON mode (per-event):
  - `ANALYTICS_MODE=json`, `ANALYTICS_URL=http://mock-apis:8000/analytics/data`
- CSV batch mode:
  - `ANALYTICS_MODE=csv`, `ANALYTICS_URL=http://mock-apis:8000/analytics/upload`
  - Tune `BATCH_MAX_SIZE`, `FLUSH_INTERVAL_SECS`.

## Troubleshooting

- Producer metrics panel empty
  - Ensure JMX ports 9404 are exposed (already configured in producer Dockerfiles) and Prometheus job `java-producers-jmx` is up.
- Grafana shows "No data"
  - Ensure counters have recent samples (clear Redis or lower TTL to generate posts).
  - Expand time range to 1h and refresh.
- HTTP 422 from Analytics
  - Mock API accepts any JSON; for CSV ensure `Content-Type: text/csv`.
