"""兑换接口自动化测试（范本，后续需要你继续补全）。

接口契约（已用 OpenAPI + 实际请求核对）：
- POST /redeem/verify  必填字段只有 code；未知兑换码返回 200 + valid=false。
- POST /redeem/confirm 必填 email + code；email 走 EmailStr 校验。

已覆盖：未知码、缺字段、非法邮箱。
待你补全：有效码整条链路、过期码、已使用码、Team 满员、重复兑换的幂等性。
"""

import pytest

UNKNOWN_CODE = "NOT-A-REAL-CODE"


class TestRedeemVerify:
    def test_unknown_code_is_invalid(self, client):
        resp = client.post("/redeem/verify", json={"code": UNKNOWN_CODE})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["valid"] is False
        assert body["reason"] == "兑换码不存在"
        assert body["teams"] == []

    @pytest.mark.parametrize("payload", [{}, {"code": ""}])
    def test_missing_or_empty_code_returns_422(self, client, payload):
        assert client.post("/redeem/verify", json=payload).status_code == 422

    def test_extra_email_field_is_ignored(self, client):
        """verify 接口只声明了 code，多传 email 不应影响结果（当前契约是忽略）。"""
        resp = client.post(
            "/redeem/verify",
            json={"email": "someone@example.com", "code": UNKNOWN_CODE},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is False


class TestRedeemConfirm:
    def test_invalid_email_format_returns_422(self, client):
        resp = client.post("/redeem/confirm", json={"email": "not-an-email", "code": "X"})
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert any(item["loc"][-1] == "email" for item in detail)

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"email": "someone@example.com"},
            {"code": "ONLY-CODE"},
        ],
    )
    def test_missing_field_returns_422(self, client, payload):
        assert client.post("/redeem/confirm", json=payload).status_code == 422

    def test_unknown_code_reports_no_available_team(self, client):
        """记录当前实现的真实行为：业务失败返回 500，属于待改进项（应改为 4xx）。"""
        resp = client.post(
            "/redeem/confirm",
            json={"email": "someone@example.com", "code": UNKNOWN_CODE},
        )
        assert resp.status_code == 500
        assert resp.json()["detail"] == "没有可用的 Team"


class TestWarrantyCheck:
    def test_email_without_warranty(self, client):
        resp = client.post("/warranty/check", json={"email": "someone@example.com"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["has_warranty"] is False
        assert body["can_reuse"] is False

@pytest.fixture
def demo_code(admin_client):
    """测试库是干净的，所以要先造一张兑换码出来"""
    admin_client.post("/admin/codes/generate", json={"type": "single", "code": "DEMO2026"})


def test_uppercase_code_is_valid(client, demo_code):
    """大写码能通过校验——这是当前的正常行为，要守住"""
    resp = client.post("/redeem/verify", json={"code": "DEMO2026"})
    assert resp.json()["valid"] is True


@pytest.mark.xfail(reason="已知缺陷 001：小写码被判为不存在，修复后应通过")
def test_lowercase_code_should_be_valid(client, demo_code):
    """期望：同一个码的大小写应该等价。当前实现不满足，见缺陷报告 001"""
    resp = client.post("/redeem/verify", json={"code": "demo2026"})
    assert resp.json()["valid"] is True