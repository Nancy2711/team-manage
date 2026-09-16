import pytest


@pytest.mark.parametrize("count", [1, 2, 500, 999, 1000])
def test_generate_codes_with_valid_count(admin_client, count):
    resp = admin_client.post("/admin/codes/generate", json={"type": "batch", "count": count})
    assert resp.status_code == 200
    assert resp.json()["total"] == count


@pytest.mark.parametrize("count", [0, -1, 1001, None])
def test_generate_codes_with_invalid_count(admin_client, count):
    resp = admin_client.post("/admin/codes/generate", json={"type": "batch", "count": count})
    assert resp.status_code == 400


@pytest.mark.parametrize("count", ["abc", 1.19])
def test_generate_codes_with_wrong_type(admin_client, count):
    resp = admin_client.post("/admin/codes/generate", json={"type": "batch", "count": count})
    assert resp.status_code == 422


def test_generate_codes_without_count(admin_client):
    resp = admin_client.post("/admin/codes/generate", json={"type": "batch"})
    assert resp.status_code == 400