from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Gerenciador de Tarefas", description="API CRUD de tarefas em memória.")


class TarefaIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=100, examples=["Estudar FastAPI"])
    descricao: str | None = Field(default=None, max_length=500)
    concluida: bool = False


class Tarefa(TarefaIn):
    id: int


tarefas: dict[int, Tarefa] = {}
proximo_id = 1


def buscar(tarefa_id: int) -> Tarefa:
    if tarefa_id not in tarefas:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarefa não encontrada")
    return tarefas[tarefa_id]


@app.get("/tarefas", response_model=list[Tarefa], tags=["Tarefas"])
def listar(concluida: bool | None = None):
    """Lista tarefas. Filtro opcional por query parameter `concluida`."""
    return [t for t in tarefas.values() if concluida is None or t.concluida == concluida]


@app.get("/tarefas/{tarefa_id}", response_model=Tarefa, tags=["Tarefas"])
def obter(tarefa_id: int):
    return buscar(tarefa_id)


@app.post("/tarefas", response_model=Tarefa, status_code=status.HTTP_201_CREATED, tags=["Tarefas"])
def criar(dados: TarefaIn):
    global proximo_id
    tarefa = Tarefa(id=proximo_id, **dados.model_dump())
    tarefas[proximo_id] = tarefa
    proximo_id += 1
    return tarefa


@app.put("/tarefas/{tarefa_id}", response_model=Tarefa, tags=["Tarefas"])
def atualizar(tarefa_id: int, dados: TarefaIn):
    buscar(tarefa_id)
    tarefas[tarefa_id] = Tarefa(id=tarefa_id, **dados.model_dump())
    return tarefas[tarefa_id]


@app.delete("/tarefas/{tarefa_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tarefas"])
def remover(tarefa_id: int):
    buscar(tarefa_id)
    del tarefas[tarefa_id]
