from fastapi.testclient import TestClient

from main import app

c = TestClient(app)


def test_crud():
    r = c.post("/tarefas", json={"titulo": "Estudar"})
    assert r.status_code == 201
    id = r.json()["id"]
    assert c.get(f"/tarefas/{id}").json()["titulo"] == "Estudar"
    assert c.put(f"/tarefas/{id}", json={"titulo": "Feito", "concluida": True}).json()["concluida"]
    assert len(c.get("/tarefas?concluida=true").json()) == 1
    assert c.post("/tarefas", json={"titulo": ""}).status_code == 422
    assert c.delete(f"/tarefas/{id}").status_code == 204    
    assert c.get(f"/tarefas/{id}").status_code == 404   