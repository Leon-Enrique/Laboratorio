def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data


def test_api_root_not_found(client):
    response = client.get("/api/v1/ordenes/")
    assert response.status_code in (401, 403)
