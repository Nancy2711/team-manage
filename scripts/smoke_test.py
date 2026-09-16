"""部署后冒烟测试脚本：对真实启动的服务打接口。

用法：
    python scripts/smoke_test.py                      # 默认 http://127.0.0.1:8008
    python scripts/smoke_test.py http://host:port

退出码 0 表示全部通过，非 0 表示有检查项失败，可直接用于 CI 的部署后验证步骤。
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8008"
ADMIN_PASSWORD = "admin123"

results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((name, condition, detail))


def request(path: str, payload: dict | None = None, method: str | None = None,
            headers: dict | None = None) -> tuple[int, str]:
    data = json.dumps(payload).encode() if payload is not None else None
    hdrs = {"Content-Type": "application/json"} if data else {}
    hdrs.update(headers or {})
    req = urllib.request.Request(BASE + path, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, (exc.read() or b"").decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


def main() -> int:
    status, body = request("/health")
    check("GET /health 返回 200", status == 200, f"status={status}")
    check("健康检查返回 healthy", "healthy" in body, body[:120])

    status, _ = request("/docs")
    check("GET /docs 可访问", status == 200, f"status={status}")

    status, body = request("/openapi.json")
    check("GET /openapi.json 可访问", status == 200, f"status={status}")
    check("接口数量 >= 30", body.count('"/') >= 30, f"paths≈{body.count('  /')}")

    status, _ = request("/auth/login", {"password": "wrong-password"})
    check("错误密码返回 401", status == 401, f"status={status}")

    status, body = request("/auth/login", {"password": ADMIN_PASSWORD})
    check("管理员登录成功", status == 200 and '"success":true' in body.replace(" ", ""), f"status={status} {body[:100]}")

    status, body = request("/redeem/verify", {"email": "smoke@example.com", "code": "SMOKE-CODE"})
    check("无效兑换码被拒绝", status == 200 and '"valid":false' in body.replace(" ", ""), f"status={status} {body[:100]}")

    status, _ = request("/admin/", headers={"accept": "application/json"})
    check("未登录访问管理台被拦截", status in (401, 403), f"status={status}")

    width = max(len(name) for name, _, _ in results)
    failed = 0
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"[{mark}] {name.ljust(width)}  {detail if not ok else ''}")

    print(f"\n{len(results) - failed}/{len(results)} 项通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
