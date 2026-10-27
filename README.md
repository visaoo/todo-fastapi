# Gerenciador de Tarefas — FastAPI

API RESTful com CRUD completo de tarefas, armazenadas em memória (sem db) e validadas com Pydantic.

## Integrantes

- Fillype Oliveira Amorim
- Gabriel Correa de Abreu Guanais

## Rodar localmente

Requisitos: Python 3.10+

```bash
git clone https://github.com/visaoo/todo-fastapi.git
cd todo-fastapi
python -m venv .venv
# windows: .venv\Scripts\activate | wsl - mac - linux: source .venv/bin/activate
pip install -r requirements.txt
fastapi dev main.py
```

A API sobe em http://127.0.0.1:8000. Documentação automática:

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

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
pytest
```