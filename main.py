from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from auth import ERRO_401, Erro, router as auth_router, usuario_atual
from database import get_db

app = FastAPI(
    title="Gerenciador de Tarefas",
    version="1.0.0",
    description="""
API CRUD de tarefas com **SQLite**, **SQLAlchemy** e autenticação **OAuth2 + JWT**.

### Como usar
1. Cadastre um usuário em `POST /usuarios`.
2. Clique em **Authorize** 🔓 e faça login com e-mail e senha.
3. As rotas de escrita (`POST`, `PUT`, `DELETE`) passam a aceitar suas requisições.

As rotas de leitura (`GET`) são públicas.
""",
    openapi_tags=[
        {"name": "Autenticação", "description": "Cadastro de usuários e emissão do token JWT."},
        {"name": "Tarefas", "description": "CRUD de tarefas. Escrita exige token (🔒)."},
    ],
)

app.include_router(auth_router)

DB = Annotated[Session, Depends(get_db)]
# POST/PUT/DELETE exigem JWT; GETs ficam públicos
PROTEGIDA = [Depends(usuario_atual)]
TarefaId = Annotated[int, Path(description="ID da tarefa", examples=[1])]

ERRO_404: dict[int | str, dict[str, Any]] = {404: {"model": Erro, "description": "Tarefa não encontrada"}}


class TarefaIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=100, description="Título curto da tarefa", examples=["Estudar FastAPI"])
    descricao: str | None = Field(default=None, max_length=500, description="Detalhes opcionais", examples=["Ler a doc de testes"])
    concluida: bool = Field(default=False, description="Se a tarefa já foi feita")


class Tarefa(TarefaIn):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(description="Identificador gerado pelo banco")


def buscar(db: Session, tarefa_id: int) -> models.Tarefa:
    tarefa = db.get(models.Tarefa, tarefa_id)
    if tarefa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarefa não encontrada")
    return tarefa


@app.get(
    "/tarefas",
    response_model=list[Tarefa],
    tags=["Tarefas"],
    summary="Listar tarefas",
    response_description="Lista de tarefas (pode ser vazia)",
)
def listar(
    db: DB,
    concluida: Annotated[bool | None, Query(description="Filtra por status; omita para trazer todas")] = None,
):
    """
    Retorna todas as tarefas cadastradas.

    - **concluida=true**: só as concluídas
    - **concluida=false**: só as pendentes
    """
    query = select(models.Tarefa)
    if concluida is not None:
        query = query.where(models.Tarefa.concluida == concluida)
    return db.scalars(query).all()


@app.get(
    "/tarefas/{tarefa_id}",
    response_model=Tarefa,
    tags=["Tarefas"],
    summary="Buscar tarefa por ID",
    responses=ERRO_404,
)
def obter(tarefa_id: TarefaId, db: DB):
    """Retorna uma única tarefa. Responde **404** se o ID não existir."""
    return buscar(db, tarefa_id)


@app.post(
    "/tarefas",
    response_model=Tarefa,
    status_code=status.HTTP_201_CREATED,
    tags=["Tarefas"],
    summary="Criar tarefa 🔒",
    response_description="Tarefa criada, com o ID gerado",
    dependencies=PROTEGIDA,
    responses=ERRO_401,
)
def criar(dados: TarefaIn, db: DB):
    """
    Cria uma nova tarefa. **Exige token JWT.**

    O `titulo` é obrigatório (1 a 100 caracteres); `descricao` e `concluida` são opcionais.
    """
    tarefa = models.Tarefa(**dados.model_dump())
    db.add(tarefa)
    db.commit()
    db.refresh(tarefa)
    return tarefa


@app.put(
    "/tarefas/{tarefa_id}",
    response_model=Tarefa,
    tags=["Tarefas"],
    summary="Atualizar tarefa 🔒",
    dependencies=PROTEGIDA,
    responses=ERRO_401 | ERRO_404,
)
def atualizar(tarefa_id: TarefaId, dados: TarefaIn, db: DB):
    """Substitui todos os campos da tarefa pelos enviados. **Exige token JWT.**"""
    tarefa = buscar(db, tarefa_id)
    for campo, valor in dados.model_dump().items():
        setattr(tarefa, campo, valor)
    db.commit()
    db.refresh(tarefa)
    return tarefa


@app.delete(
    "/tarefas/{tarefa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tarefas"],
    summary="Remover tarefa 🔒",
    response_description="Tarefa removida (sem corpo)",
    dependencies=PROTEGIDA,
    responses=ERRO_401 | ERRO_404,
)
def remover(tarefa_id: TarefaId, db: DB):
    """Apaga a tarefa definitivamente. **Exige token JWT.**"""
    db.delete(buscar(db, tarefa_id))
    db.commit()
