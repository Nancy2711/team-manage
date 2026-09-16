import httpx

from app.services.notification import notification_service


class FakeResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("server error", request=None, response=None)


class FakeAsyncClient:
    last_instance = None
    next_status = 200

    def __init__(self, *args, **kwargs):
        self.calls = []
        FakeAsyncClient.last_instance = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json=None, headers=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return FakeResponse(FakeAsyncClient.next_status)


async def test_webhook_sends_correct_payload(monkeypatch):
    FakeAsyncClient.next_status = 200
    monkeypatch.setattr("app.services.notification.httpx.AsyncClient", FakeAsyncClient)

    result = await notification_service.send_webhook_notification("http://example.com/hook", 3, 10)

    assert result is True
    call = FakeAsyncClient.last_instance.calls[0]
    assert call["url"] == "http://example.com/hook"
    assert call["json"]["event"] == "low_stock"
    assert call["json"]["current_seats"] == 3
    assert call["json"]["threshold"] == 10


async def test_webhook_includes_api_key_header(monkeypatch):
    FakeAsyncClient.next_status = 200
    monkeypatch.setattr("app.services.notification.httpx.AsyncClient", FakeAsyncClient)

    result = await notification_service.send_webhook_notification(
        "http://example.com/hook", 3, 10, api_key="SECRET123"
    )

    assert result is True
    assert FakeAsyncClient.last_instance.calls[0]["headers"]["X-API-Key"] == "SECRET123"


async def test_webhook_returns_false_on_server_error(monkeypatch):
    FakeAsyncClient.next_status = 500
    monkeypatch.setattr("app.services.notification.httpx.AsyncClient", FakeAsyncClient)

    result = await notification_service.send_webhook_notification("http://example.com/hook", 3, 10)

    assert result is False


async def test_webhook_returns_false_on_network_error(monkeypatch):
    class BoomClient(FakeAsyncClient):
        async def post(self, url, json=None, headers=None):
            raise httpx.ConnectError("network down")

    monkeypatch.setattr("app.services.notification.httpx.AsyncClient", BoomClient)

    result = await notification_service.send_webhook_notification("http://example.com/hook", 3, 10)

    assert result is False


async def test_webhook_message_contains_numbers(monkeypatch):
    """通知文案里应该带上具体的数字（剩几个、阈值多少）"""
    FakeAsyncClient.next_status = 200
    monkeypatch.setattr("app.services.notification.httpx.AsyncClient", FakeAsyncClient)

    await notification_service.send_webhook_notification("http://example.com/hook", 3, 10)

    message = FakeAsyncClient.last_instance.calls[0]["json"]["message"]
    assert "3" in message
    assert "10" in message
