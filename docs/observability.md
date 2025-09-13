# Observability

## Metrics

- Producers (Spring Boot): exported via JMX Exporter on port 9404 (configured in producer Dockerfiles), scraped by Prometheus job `java-producers-jmx`.
- Python consumer: Prometheus text on `/` (port 9108), job `python-consumer`.
- Mock APIs: `/metrics`, job `mock-apis`.

## Dashboard

- Grafana is provisioned with a Prometheus datasource and a dashboard `Kafka Integration Overview`.
- Panels include:
  - Consumer message rate, dedup skips
  - Analytics POST success/fail rate and latency
  - Analytics DLQ rate
  - Mock Analytics received rate
  - Producer records/sec (per topic) — powered by JMX exporter per-topic metrics

### Sample Screenshot

![Grafana Dashboard](https://res.cloudinary.com/dlwzb2uh3/image/upload/fl_preserve_transparency/v1757799669/Screenshot_2025-09-13_at_23.27.16_paxvuo.jpg?_s=public-apps)

## Logs

- Structured logging in the Python consumer (key=value style) with context (topic, key, mode, status).
- Java producers log publish confirmations and polling summaries.

## Alerts

- Provisioned in `infrastructure/grafana-provisioning/alerting/`:
  - Contact point: `contact-points.yml` (set your webhook URL)
  - Rules: `rules.yml` (fail rate and DLQ rate over 5m)
  - Scrape target down
