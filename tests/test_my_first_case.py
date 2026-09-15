import pytest


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_docs_available(client):
    assert client.get("/docs").status_code == 200


def test_openapi_available(client):
    assert client.get("/openapi.json").status_code == 200


def test_admin_requires_login(client):
    resp = client.get("/admin/", headers={"accept": "application/json"})
    assert resp.status_code == 401


@pytest.mark.parametrize("wrong_password", ["123456", "admin", "admin1234"])
def test_login_wrong_password_returns_401(client, wrong_password):
    resp = client.post("/auth/login", json={"password": wrong_password})
    assert resp.status_code == 401