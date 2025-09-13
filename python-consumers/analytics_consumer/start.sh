#!/usr/bin/env bash
set -euo pipefail

wait_for_host() {
  local host="$1"; local port="$2"; local name="$3"; local timeout="${4:-60}"
  echo "Waiting for $name at $host:$port (timeout ${timeout}s) ..."
  for i in $(seq 1 "$timeout"); do
    if (echo > "/dev/tcp/$host/$port") >/dev/null 2>&1; then
      echo "$name is up"
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for $name at $host:$port" >&2
  return 1
}

KAFKA_HOST=${KAFKA_HOST:-kafka}
KAFKA_PORT=${KAFKA_PORT:-9092}
REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}
APIS_HOST=${APIS_HOST:-mock-apis}
APIS_PORT=${APIS_PORT:-8000}

wait_for_host "$KAFKA_HOST" "$KAFKA_PORT" "Kafka"
wait_for_host "$REDIS_HOST" "$REDIS_PORT" "Redis"
wait_for_host "$APIS_HOST" "$APIS_PORT" "Mock APIs"

exec python /app/main.py
