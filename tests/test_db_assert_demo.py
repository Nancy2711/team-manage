def test_generate_codes_actually_writes_to_db(admin_client, db_conn):
    """接口返回成功，不代表数据真的落库了——去数据库里查一下才算数"""
    resp = admin_client.post("/admin/codes/generate", json={"type": "batch", "count": 3})
    assert resp.status_code == 200

    rows = db_conn.execute("SELECT code, status FROM redemption_codes").fetchall()
    print("\n  数据库里实际有:", rows)

    assert len(rows) == 3
    assert all(status == "unused" for _, status in rows)

def test_generated_codes_match_api_response(admin_client, db_conn):
    """接口说生成了哪几张，数据库里就该有哪几张——两边必须一致"""
    resp = admin_client.post("/admin/codes/generate", json={"type": "batch", "count": 3})
    api_codes = set(resp.json()["codes"])

    db_codes = {row[0] for row in db_conn.execute("SELECT code FROM redemption_codes")}

    assert api_codes == db_codes
    assert len(db_codes) == 3