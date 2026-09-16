from datetime import timedelta

from app.utils.time_utils import get_now


def test_code_is_valid_before_expiry(client, admin_client):
    """刚生成的、1 天有效期的兑换码，现在应该有效"""
    admin_client.post("/admin/codes/generate",
                      json={"type": "single", "code": "TIME001", "expires_days": 1})

    resp = client.post("/redeem/verify", json={"code": "TIME001"})
    assert resp.json()["valid"] is True


def test_code_is_rejected_after_expiry(client, admin_client, monkeypatch):
    """把时间拨到 10 天后，同一个兑换码应该被判为过期"""
    admin_client.post("/admin/codes/generate",
                      json={"type": "single", "code": "TIME002", "expires_days": 1})

    future = get_now() + timedelta(days=10)
    monkeypatch.setattr("app.services.redemption.get_now", lambda: future)

    resp = client.post("/redeem/verify", json={"code": "TIME002"})
    assert resp.json()["valid"] is False
    assert "过期" in resp.json()["reason"]