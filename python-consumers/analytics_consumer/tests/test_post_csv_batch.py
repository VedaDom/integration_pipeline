import asyncio
import json
import pytest

from analytics_consumer.main import post_csv_batch

class FakeProducer:
    def __init__(self):
        self.sent = []
    async def send_and_wait(self, topic, value):
        self.sent.append((topic, value))

class OkTransport:
    def __init__(self, status=200):
        self.status = status
    def handle_request(self, request):
        import httpx
        return httpx.Response(self.status, request=request)

@pytest.mark.asyncio
async def test_post_csv_batch_success(monkeypatch):
    # Arrange a transport that returns 200 OK
    import httpx
    transport = httpx.MockTransport(lambda req: httpx.Response(200, request=req))
    orig_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kwargs: orig_client(transport=transport))

    producer = FakeProducer()
    payload_csv = "type,customer_id\ncustomer_update,c1\n"

    # Act
    await post_csv_batch(payload_csv, "http://example/analytics/upload", producer, "analytics_dlq")

    # Assert: no DLQ
    assert producer.sent == []

@pytest.mark.asyncio
async def test_post_csv_batch_failure_goes_to_dlq(monkeypatch):
    # Arrange a transport that returns 500
    import httpx
    transport = httpx.MockTransport(lambda req: httpx.Response(500, request=req))
    orig_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kwargs: orig_client(transport=transport))

    producer = FakeProducer()
    payload_csv = "type,customer_id\ncustomer_update,c1\n"

    # Act: should raise and publish to DLQ
    with pytest.raises(Exception):
        await post_csv_batch(payload_csv, "http://example/analytics/upload", producer, "analytics_dlq")

    # Assert
    assert len(producer.sent) == 1
    topic, value = producer.sent[0]
    assert topic == "analytics_dlq"
    envelope = json.loads(value.decode("utf-8"))
    assert envelope["error"].startswith("analytics_http_")
