import asyncio
import os
import signal
from typing import Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import redis.asyncio as redis
import hashlib
import json
import time
import logging
import httpx
from prometheus_client import Counter, Histogram, start_http_server
from io import StringIO
import csv

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
CUSTOMER_TOPIC = os.getenv("CUSTOMER_TOPIC", "customer_data")
INVENTORY_TOPIC = os.getenv("INVENTORY_TOPIC", "inventory_data")
ANALYTICS_DLQ_TOPIC = os.getenv("ANALYTICS_DLQ_TOPIC", "analytics_dlq")
ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://localhost:8000/analytics/data")
ANALYTICS_MODE = os.getenv("ANALYTICS_MODE", "json").lower()  # json | csv
BATCH_MAX_SIZE = int(os.getenv("BATCH_MAX_SIZE", "50"))
FLUSH_INTERVAL_SECS = float(os.getenv("FLUSH_INTERVAL_SECS", "10"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
IDEMP_TTL_SECONDS = int(os.getenv("IDEMP_TTL_SECONDS", "86400"))  # 1 day default
METRICS_PORT = int(os.getenv("METRICS_PORT", "9108"))

# Set up structured logging (simple key=val style)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s level=%(levelname)s msg=%(message)s")
log = logging.getLogger("analytics_consumer")

# Prometheus metrics
MSG_COUNTER = Counter("consumer_messages_total", "Messages consumed", ["topic"]) 
DEDUP_COUNTER = Counter("consumer_dedup_skipped_total", "Messages skipped due to idempotency", ["topic"]) 
ANALYTICS_SUCCESS = Counter("analytics_post_success_total", "Successful analytics POSTs")
ANALYTICS_FAIL = Counter("analytics_post_fail_total", "Failed analytics POSTs")
DLQ_COUNTER = Counter("analytics_dlq_total", "Messages published to analytics DLQ")
POST_LATENCY = Histogram("analytics_post_latency_seconds", "Latency of analytics POSTs in seconds")
BATCH_ROWS = Counter("analytics_batch_rows_total", "Total rows included in analytics batches")
BATCH_COUNT = Counter("analytics_batches_total", "Total analytics batches sent")

async def post_csv_batch(payload_csv: str, url: str, producer: AIOKafkaProducer, dlq_topic: str) -> None:
    """Post CSV batch to analytics; on failure, publish to DLQ and raise."""
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, content=payload_csv, headers={"Content-Type": "text/csv"})
            POST_LATENCY.observe(time.perf_counter() - start)
            if 200 <= resp.status_code < 300:
                ANALYTICS_SUCCESS.inc()
                BATCH_COUNT.inc()
                rows = payload_csv.count("\n") - 1
                log.info(f"analytics_post_ok mode=csv rows={rows} status={resp.status_code}")
                return
            else:
                ANALYTICS_FAIL.inc()
                raise RuntimeError(f"analytics_http_{resp.status_code}")
    except Exception as e:
        ANALYTICS_FAIL.inc()
        envelope = {"error": str(e), "source_mode": "csv", "payload_rows": max(0, (payload_csv.count('\n')-1))}
        try:
            await producer.send_and_wait( dlq_topic, json.dumps(envelope).encode("utf-8") )
            DLQ_COUNTER.inc()
            log.error(f"analytics_post_fail mode=csv rows={envelope['payload_rows']} dlq_topic={dlq_topic} error={e}")
        except Exception as e2:
            log.error(f"dlq_publish_failed mode=csv error={e2}")
        raise

def build_csv_from_events(events: list[dict]) -> str:
    """Build CSV payload from merged events."""
    csv_buf = StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow(["type", "customer_id", "product_id", "status", "sku", "qty", "total_products", "low_stock_count", "total_customers"]) 
    for ev in events:
        if ev.get("type") == "customer_update":
            cust = ev.get("customer", {})
            inv = ev.get("inventory_summary", {})
            writer.writerow([
                ev.get("type"),
                cust.get("id"),
                "",
                cust.get("status"),
                "",
                "",
                inv.get("total_products"),
                inv.get("low_stock_count"),
                "",
            ])
        elif ev.get("type") == "inventory_update":
            prod = ev.get("product", {})
            custs = ev.get("customer_summary", {})
            writer.writerow([
                ev.get("type"),
                "",
                prod.get("product_id"),
                "",
                prod.get("sku"),
                prod.get("qty"),
                "",
                "",
                custs.get("total_customers"),
            ])
    return csv_buf.getvalue()

async def consume():
    r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    consumer = AIOKafkaConsumer(
        CUSTOMER_TOPIC,
        INVENTORY_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=os.getenv("CONSUMER_GROUP", "analytics-consumers"),
        enable_auto_commit=True,
        auto_offset_reset="earliest",
    )
    # In-memory stores for a lightweight merge/co-group
    customers = {}
    products = {}
    batch = []  # holds merged events until flush
    last_flush = time.monotonic()

    await producer.start()
    await consumer.start()

    try:
        # Warm up Redis connection
        try:
            await r.ping()
        except Exception as e:
            log.warning(f"Redis not reachable at {REDIS_URL}: {e}. Proceeding without idempotency.")

        # Start Prometheus metrics HTTP server
        start_http_server(METRICS_PORT)
        log.info(f"metrics_port={METRICS_PORT} analytics_url={ANALYTICS_URL} analytics_mode={ANALYTICS_MODE} batch_max={BATCH_MAX_SIZE} flush_interval={FLUSH_INTERVAL_SECS} kafka_bootstrap={KAFKA_BOOTSTRAP_SERVERS}")
        log.info(f"Consuming topics: {CUSTOMER_TOPIC}, {INVENTORY_TOPIC}")

        async def flush_batch_if_needed(force: bool = False):
            nonlocal batch, last_flush
            if ANALYTICS_MODE == "json":
                # For json mode, send immediately per event (handled inline), nothing to flush
                return
            now = time.monotonic()
            if not force and len(batch) < 1:
                return
            if not force and len(batch) < BATCH_MAX_SIZE and (now - last_flush) < FLUSH_INTERVAL_SECS:
                return
            # Build CSV
            payload_csv = build_csv_from_events(batch)
            rows = max(0, len(batch))
            batch = []
            last_flush = now
            try:
                await post_csv_batch(payload_csv, ANALYTICS_URL, producer, ANALYTICS_DLQ_TOPIC)
                BATCH_ROWS.inc(rows)
            except Exception:
                pass

        async for msg in consumer:
            key_bytes = msg.key if msg.key is not None else b""
            key_str = key_bytes.decode("utf-8", errors="ignore") if isinstance(key_bytes, (bytes, bytearray)) else str(key_bytes)
            digest = hashlib.sha256(msg.value or b"").hexdigest()
            redis_key = f"processed:{msg.topic}:{key_str}"

            skip = False
            try:
                prev = await r.get(redis_key)
                if prev == digest:
                    skip = True
                else:
                    await r.set(redis_key, digest, ex=IDEMP_TTL_SECONDS)
            except Exception:
                # If Redis is unavailable, fall back to processing without dedup
                pass

            if skip:
                # Uncomment for verbose dedup logging
                DEDUP_COUNTER.labels(topic=msg.topic).inc()
                # log.debug(f"DEDUP skip topic={msg.topic} key={key_str}")
                continue

            MSG_COUNTER.labels(topic=msg.topic).inc()

            try:
                payload = json.loads(msg.value.decode("utf-8"))
            except Exception:
                payload = None

            merged = None
            if msg.topic == CUSTOMER_TOPIC and payload:
                customers[key_str] = payload
                # Lightweight merge: customer + inventory summary
                inv_total = len(products)
                low_stock = sum(1 for p in products.values() if isinstance(p.get("qty"), int) and p.get("qty", 0) < 20)
                merged = {
                    "type": "customer_update",
                    "customer": payload,
                    "inventory_summary": {"total_products": inv_total, "low_stock_count": low_stock},
                }
            elif msg.topic == INVENTORY_TOPIC and payload:
                products[key_str] = payload
                cust_total = len(customers)
                merged = {
                    "type": "inventory_update",
                    "product": payload,
                    "customer_summary": {"total_customers": cust_total},
                }

            if merged is None:
                log.warning(f"skip_unmerged topic={msg.topic} key={key_str}")
                continue

            # Deliver either per-event JSON or batched CSV
            if ANALYTICS_MODE == "json":
                start = time.perf_counter()
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        resp = await client.post(ANALYTICS_URL, json=merged)
                        POST_LATENCY.observe(time.perf_counter() - start)
                        if 200 <= resp.status_code < 300:
                            ANALYTICS_SUCCESS.inc()
                            log.info(f"analytics_post_ok key={key_str} topic={msg.topic} status={resp.status_code}")
                        else:
                            ANALYTICS_FAIL.inc()
                            raise RuntimeError(f"analytics_http_{resp.status_code}")
                except Exception as e:
                    ANALYTICS_FAIL.inc()
                    envelope = {
                        "error": str(e),
                        "source_topic": msg.topic,
                        "key": key_str,
                        "payload": merged,
                    }
                    try:
                        await producer.send_and_wait(ANALYTICS_DLQ_TOPIC, json.dumps(envelope).encode("utf-8"), key=key_bytes)
                        DLQ_COUNTER.inc()
                        log.error(f"analytics_post_fail key={key_str} dlq_topic={ANALYTICS_DLQ_TOPIC} error={e}")
                    except Exception as e2:
                        log.error(f"dlq_publish_failed key={key_str} error={e2}")
            else:
                # csv mode: stage into batch and flush if needed
                batch.append(merged)
                await flush_batch_if_needed(force=False)

            # time-based flush
            await flush_batch_if_needed(force=False)
    finally:
        await consumer.stop()
        try:
            # flush remaining CSV batch
            if ANALYTICS_MODE == "csv":
                # best-effort flush
                try:
                    await flush_batch_if_needed(force=True)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            await producer.stop()
        except Exception:
            pass
        try:
            await r.close()
        except Exception:
            pass

async def main():
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, stop.set)

    consumer_task = asyncio.create_task(consume())
    await stop.wait()
    consumer_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await consumer_task

if __name__ == "__main__":
    import contextlib
    asyncio.run(main())
