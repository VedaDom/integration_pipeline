# Python Consumers (Analytics)

An async consumer reads from Kafka topics `customer_data` and `inventory_data`, merges data, enforces idempotency via Redis, and posts to an Analytics endpoint or writes CSV.

Key libraries: aiokafka, httpx, pydantic, redis, prometheus-client.

Config (env):
- KAFKA_BOOTSTRAP_SERVERS (default: localhost:9092)
- REDIS_URL (default: redis://localhost:6379/0)
- ANALYTICS_URL (default: http://localhost:9000/analytics/data)

Run (placeholder):
```
python -m analytics_consumer.main
```
