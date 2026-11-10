from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from auth import router as auth_router, usuario_atual
from database import get_db

app = FastAPI(title="Gerenciador de Tarefas", description="API CRUD de tarefas com SQLite e autenticação JWT.")

app.include_router(auth_router)

DB = Annotated[Session, Depends(get_db)]
# POST/PUT/DELETE exigem JWT; GETs ficam públicos
PROTEGIDA = [Depends(usuario_atual)]


class TarefaIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=100, examples=["Estudar FastAPI"])
    descricao: str | None = Field(default=None, max_length=500)
    concluida: bool = False


class Tarefa(TarefaIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


def buscar(db: Session, tarefa_id: int) -> models.Tarefa:
    tarefa = db.get(models.Tarefa, tarefa_id)
    if tarefa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarefa não encontrada")
    return tarefa


@app.get("/tarefas", response_model=list[Tarefa], tags=["Tarefas"])
def listar(db: DB, concluida: bool | None = None):
    """Lista tarefas. Filtro opcional por query parameter `concluida`."""
    query = select(models.Tarefa)
    if concluida is not None:
        query = query.where(models.Tarefa.concluida == concluida)
    return db.scalars(query).all()


@app.get("/tarefas/{tarefa_id}", response_model=Tarefa, tags=["Tarefas"])
def obter(tarefa_id: int, db: DB):
    return buscar(db, tarefa_id)


@app.post("/tarefas", response_model=Tarefa, status_code=status.HTTP_201_CREATED, tags=["Tarefas"], dependencies=PROTEGIDA)
def criar(dados: TarefaIn, db: DB):
    tarefa = models.Tarefa(**dados.model_dump())
    db.add(tarefa)
    db.commit()
    db.refresh(tarefa)
    return tarefa


@app.put("/tarefas/{tarefa_id}", response_model=Tarefa, tags=["Tarefas"], dependencies=PROTEGIDA)
def atualizar(tarefa_id: int, dados: TarefaIn, db: DB):
    tarefa = buscar(db, tarefa_id)
    for campo, valor in dados.model_dump().items():
        setattr(tarefa, campo, valor)
    db.commit()
    db.refresh(tarefa)
    return tarefa


@app.delete("/tarefas/{tarefa_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tarefas"], dependencies=PROTEGIDA)
def remover(tarefa_id: int, db: DB):
    db.delete(buscar(db, tarefa_id))
    db.commit()
