from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app

# Banco em memória só para os testes, sem tocar no tarefas.db
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestSession = sessionmaker(bind=engine)


def get_test_db():
    with TestSession() as db:
        yield db


app.dependency_overrides[get_db] = get_test_db
c = TestClient(app)


def test_auth():
    usuario = {"email": "ana@example.com", "senha": "segredo123"}
    assert c.post("/usuarios", json=usuario).status_code == 201
    assert c.post("/usuarios", json=usuario).status_code == 409
    assert c.post("/token", data={"username": usuario["email"], "password": "errada"}).status_code == 401
    assert c.post("/tarefas", json={"titulo": "x"}).status_code == 401
    assert c.post("/tarefas", json={"titulo": "x"}, headers={"Authorization": "Bearer lixo"}).status_code == 401
    token = c.post("/token", data={"username": usuario["email"], "password": usuario["senha"]}).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"


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
