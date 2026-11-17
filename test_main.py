import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app

# Banco em memória só para os testes, sem tocar no tarefas.db
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)


def get_test_db():
    with TestSession() as db:
        yield db


app.dependency_overrides[get_db] = get_test_db
USUARIO = {"email": "ana@example.com", "senha": "segredo123"}


@pytest.fixture
def client():
    """Cliente com banco zerado a cada teste, para os testes não dependerem da ordem."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return TestClient(app)


@pytest.fixture
def auth(client):
    """Cadastra um usuário, faz login e devolve o header Authorization."""
    client.post("/usuarios", json=USUARIO)
    r = client.post("/token", data={"username": USUARIO["email"], "password": USUARIO["senha"]})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_listar_tarefas_retorna_200(client):
    r = client.get("/tarefas")
    assert r.status_code == 200
    assert r.json() == []


def test_tarefa_inexistente_retorna_404(client):
    r = client.get("/tarefas/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "Tarefa não encontrada"}


def test_criar_sem_token_retorna_401(client):
    assert client.post("/tarefas", json={"titulo": "x"}).status_code == 401


def test_criar_com_token_invalido_retorna_401(client):
    r = client.post("/tarefas", json={"titulo": "x"}, headers={"Authorization": "Bearer lixo"})
    assert r.status_code == 401


def test_cadastro_duplicado_retorna_409(client):
    assert client.post("/usuarios", json=USUARIO).status_code == 201
    assert client.post("/usuarios", json=USUARIO).status_code == 409


def test_login_com_senha_errada_retorna_401(client):
    client.post("/usuarios", json=USUARIO)
    r = client.post("/token", data={"username": USUARIO["email"], "password": "errada"})
    assert r.status_code == 401


def test_criar_tarefa_com_titulo_vazio_retorna_422(client, auth):
    assert client.post("/tarefas", json={"titulo": ""}, headers=auth).status_code == 422


def test_crud_completo_com_token(client, auth):
    r = client.post("/tarefas", json={"titulo": "Estudar"}, headers=auth)
    assert r.status_code == 201
    id = r.json()["id"]

    assert client.get(f"/tarefas/{id}").json()["titulo"] == "Estudar"

    r = client.put(f"/tarefas/{id}", json={"titulo": "Feito", "concluida": True}, headers=auth)
    assert r.status_code == 200
    assert r.json()["concluida"] is True
    assert len(client.get("/tarefas?concluida=true").json()) == 1
    assert client.get("/tarefas?concluida=false").json() == []

    assert client.delete(f"/tarefas/{id}", headers=auth).status_code == 204
    assert client.get(f"/tarefas/{id}").status_code == 404
