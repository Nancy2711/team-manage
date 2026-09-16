"""认证接口自动化测试（范本）。

这是给你照着写其他用例的样板，重点看三件事：
1. 用 client / admin_client fixture，不自己起服务。
2. 每个用例只断言一个明确行为，失败时能直接定位。
3. 边界和异常分支（错误密码、未登录、HTML 请求跳转）都要单独有用例。
"""

import os

import pytest

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


class TestHealthAndDocs:
    def test_health_returns_healthy(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "healthy"}

    def test_swagger_docs_available(self, client):
        assert client.get("/docs").status_code == 200

    def test_openapi_contains_auth_login_path(self, openapi_spec):
        assert "/auth/login" in openapi_spec["paths"]


class TestLogin:
    def test_login_success_sets_session_cookie(self, client):
        resp = client.post("/auth/login", json={"password": ADMIN_PASSWORD})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["error"] is None
        assert "session" in resp.cookies or "session" in client.cookies

    def test_login_wrong_password_returns_401(self, client):
        resp = client.post("/auth/login", json={"password": "definitely-wrong"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "密码错误"

    @pytest.mark.parametrize("payload", [{}, {"password": ""}])
    def test_login_invalid_payload_returns_422(self, client, payload):
        assert client.post("/auth/login", json=payload).status_code == 422

    def test_status_before_login_is_unauthenticated(self, client):
        body = client.get("/auth/status").json()
        assert body["authenticated"] is False

    def test_status_after_login_shows_admin(self, admin_client):
        body = admin_client.get("/auth/status").json()
        assert body["authenticated"] is True
        assert body["user"]["is_admin"] is True

    def test_logout_clears_session(self, admin_client):
        assert admin_client.post("/auth/logout").status_code == 200
        assert admin_client.get("/auth/status").json()["authenticated"] is False


class TestAdminAccessControl:
    def test_admin_page_requires_login(self, client):
        resp = client.get("/admin/", headers={"accept": "application/json"})
        assert resp.status_code == 401

    def test_admin_page_redirects_html_request_to_login(self, client):
        resp = client.get(
            "/admin/",
            headers={"accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code in (302, 307)
        assert resp.headers["location"] == "/login"

    def test_admin_page_accessible_after_login(self, admin_client):
        resp = admin_client.get("/admin/", headers={"accept": "text/html"})
        assert resp.status_code == 200
        assert "控制台" in resp.text
