def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_index_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
