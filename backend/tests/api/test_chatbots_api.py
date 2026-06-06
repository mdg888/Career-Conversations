import pytest
from fastapi.testclient import TestClient
from backend.src.api.main import app


@pytest.fixture
def client(tmp_db):
    return TestClient(app)


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_chatbot(client):
    resp = client.post("/api/chatbots", json={
        "name": "My Bot",
        "description": "A helpful bot",
        "tone": "friendly",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Bot"
    assert data["id"]


def test_list_chatbots(client):
    client.post("/api/chatbots", json={"name": "Bot 1"})
    client.post("/api/chatbots", json={"name": "Bot 2"})
    resp = client.get("/api/chatbots")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_get_chatbot(client):
    created = client.post("/api/chatbots", json={"name": "Fetch Me"}).json()
    resp = client.get(f"/api/chatbots/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Fetch Me"


def test_get_chatbot_not_found(client):
    resp = client.get("/api/chatbots/nonexistent")
    assert resp.status_code == 404


def test_update_chatbot(client):
    created = client.post("/api/chatbots", json={"name": "Old Name"}).json()
    resp = client.put(f"/api/chatbots/{created['id']}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_delete_chatbot(client):
    created = client.post("/api/chatbots", json={"name": "Delete Me"}).json()
    resp = client.delete(f"/api/chatbots/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/chatbots/{created['id']}").status_code == 404


def test_create_chatbot_missing_name(client):
    resp = client.post("/api/chatbots", json={})
    assert resp.status_code == 422


def test_create_chatbot_empty_name(client):
    resp = client.post("/api/chatbots", json={"name": ""})
    assert resp.status_code == 422
