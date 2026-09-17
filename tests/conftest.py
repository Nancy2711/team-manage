"""pytest 公共 fixture。

设计要点：
1. 导入 app 之前先把 DATABASE_URL 指向临时文件，避免污染开发库 team_manage.db。
2. 每个用例开始前用标准库 sqlite3 同步清空所有表；TestClient 启动时会自动重建表并
   初始化管理员密码，因此每个用例都从干净且可登录的状态出发。
3. app 的 lifespan 在关闭时会 dispose 异步引擎连接池，所以每个用例新建 TestClient
   不会出现跨事件循环复用连接的问题。
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

# --- 必须在导入 app 之前设置环境变量（pydantic-settings 中环境变量优先级高于 .env）---
TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="team-manage-tests-"))
TEST_DB_PATH = TEST_DB_DIR / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("ADMIN_PASSWORD", "admin123")
os.environ.setdefault("LOG_LEVEL", "WARNING")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]


def _drop_all_tables() -> None:
    """同步清空测试库的所有表；下一个 TestClient 启动会重建。"""
    if not TEST_DB_PATH.exists():
        return
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        names = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        for name in names:
            conn.execute(f'DROP TABLE IF EXISTS "{name}"')
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def client():
    """干净数据库 + 已完成启动流程的 TestClient。"""
    _drop_all_tables()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_client(client):
    """已登录管理员的 TestClient（session 会随 cookie 自动携带）。"""
    resp = client.post("/auth/login", json={"password": ADMIN_PASSWORD})
    assert resp.status_code == 200, f"管理员登录失败: {resp.status_code} {resp.text}"
    assert resp.json().get("success") is True
    return client


@pytest.fixture
def openapi_spec(client) -> dict:
    """取回 OpenAPI 文档，便于写接口契约类断言。"""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    return resp.json()


@pytest.fixture
def db_conn():
    """直接连到测试数据库的连接，用来验证「数据真的写进库了」。

    用法：在测试函数参数里写上 db_conn，就能执行 SQL：
        rows = db_conn.execute("SELECT code, status FROM redemption_codes").fetchall()
    """
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
