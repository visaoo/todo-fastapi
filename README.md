# Gerenciador de Tarefas — FastAPI

API RESTful com CRUD completo de tarefas, persistidas em SQLite via SQLAlchemy, com migrações gerenciadas pelo Alembic e validação com Pydantic.

## Integrantes

- Fillype Oliveira Amorim
- Gabriel Correa de Abreu Guanais

## Rodar localmente

Requisitos: Python 3.10+

```bash
git clone -b feature/persistencia-dados-migrations https://github.com/visaoo/todo-fastapi.git
cd todo-fastapi
python -m venv .venv
# windows: .venv\Scripts\activate | wsl - mac - linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head   # cria o tarefas.db
fastapi dev main.py
```

A API sobe em http://127.0.0.1:8000. Documentação automática:

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Estrutura

| Arquivo | Conteúdo |
|---------|----------|
| `database.py` | Engine do SQLite, `SessionLocal`, `Base` e a dependência `get_db` (abre/fecha a sessão a cada requisição) |
| `models.py` | Model SQLAlchemy `Tarefa` (tabela `tarefas`) |
| `main.py` | Rotas CRUD, recebendo a sessão via `Depends(get_db)` |
| `alembic/` | Ambiente de migração; `alembic/versions/` contém a migração inicial |

O arquivo `tarefas.db` é ignorado pelo Git. Rode `alembic upgrade head` para criá-lo.

### Migrações

Ao alterar `models.py`:

```bash
alembic revision --autogenerate -m "descricao da mudanca"
alembic upgrade head
```

## Rotas

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/tarefas` | Lista tarefas (query opcional `?concluida=true/false`) |
| GET | `/tarefas/{tarefa_id}` | Busca uma tarefa pelo id (path parameter) |
| POST | `/tarefas` | Cria uma tarefa |
| PUT | `/tarefas/{tarefa_id}` | Atualiza uma tarefa |
| DELETE | `/tarefas/{tarefa_id}` | Remove uma tarefa |

Exemplo de corpo (POST/PUT):

```json
{ "titulo": "Leia as docs do FastAPI", "descricao": "Ler a documentação", "concluida": false }
```

## Testes

```bash
pip install pytest
pytest   # roda com um banco em memória
```