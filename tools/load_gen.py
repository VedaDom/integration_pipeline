#!/usr/bin/env python3
"""
Simple load generator to validate ~10,000 records/hour.

Approach:
- Continuously POST new customers to Mock APIs (/customers). Producers will fetch more
  customers on the next poll cycle, increasing messages flowing through Kafka and into
  the Python consumer.
- Tune rate (customers per second) and duration.
- Observe Prometheus/Grafana metrics:
  - consumer_messages_total
  - analytics_post_success_total / _fail_total
  - analytics_records_total (from Mock APIs)

Usage:
  python tools/load_gen.py --base-url http://localhost:8000 --rate 5 --duration 120

This will POST ~600 customers in 2 minutes. Combine with producer poll interval to estimate
throughput. To reach ~10k/hour, run multiple instances or increase rate.
"""
import argparse
import asyncio
import random
import string
import time

import httpx


def rand_customer():
    cid = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return {
        "id": f"c-{int(time.time())}-{cid}",
        "email": f"{cid}@example.com",
        "name": f"User {cid}",
        "status": "active",
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--rate", type=float, default=5.0, help="customers per second")
    parser.add_argument("--duration", type=int, default=120, help="seconds")
    args = parser.parse_args()

    interval = 1.0 / max(args.rate, 0.1)
    end = time.time() + args.duration
    total = 0

    async with httpx.AsyncClient(timeout=5.0) as client:
        while time.time() < end:
            payload = rand_customer()
            try:
                r = await client.post(f"{args.base_url}/customers", json=payload)
                if r.status_code >= 200 and r.status_code < 300:
                    total += 1
                else:
                    print(f"WARN: POST /customers {r.status_code}")
            except Exception as e:
                print(f"ERROR: {e}")
            await asyncio.sleep(interval)

    print(f"Done. Posted {total} customers in {args.duration}s (~{total*3600/args.duration:.0f}/hour potential).")


if __name__ == "__main__":
    asyncio.run(main())
