# Gerenciador de Tarefas — FastAPI

API RESTful com CRUD completo de tarefas, persistidas em SQLite via SQLAlchemy, com migrações gerenciadas pelo Alembic validação com Pydantic e autenticação OAuth2 + JWT (senhas com hash via Passlib).

## Integrantes

- Fillype Oliveira Amorim
- Gabriel Correa de Abreu Guanais

## Rodar localmente

Requisitos: Python 3.10+

```bash
git clone -b feature/autenticacao-jwt https://github.com/visaoo/todo-fastapi.git
cd todo-fastapi
python -m venv .venv
# windows: .venv\Scripts\activate | wsl - mac - linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head   # cria o tarefas.db com as tabelas tarefas e usuarios
fastapi dev main.py
```

A API sobe em http://127.0.0.1:8000. Documentação automática:

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Estrutura

| Arquivo | Conteúdo |
|---------|----------|
| `database.py` | Engine do SQLite, `SessionLocal`, `Base` e a dependência `get_db` (abre/fecha a sessão a cada requisição) |
| `models.py` | Models SQLAlchemy `Tarefa` (tabela `tarefas`) e `Usuario` (tabela `usuarios`: e-mail + senha com hash) |
| `auth.py` | Hash de senha (Passlib), geração/validação do JWT (PyJWT), rotas `/usuarios` e `/token` e a dependência `usuario_atual` |
| `main.py` | Rotas CRUD de tarefas; POST/PUT/DELETE exigem token via `Depends(usuario_atual)` |
| `alembic/` | Ambiente de migração; `alembic/versions/` contém as migrações |

O arquivo `tarefas.db` é ignorado pelo Git. Rode `alembic upgrade head` para criá-lo.

### Migrações

Ao alterar `models.py`:

```bash
alembic revision --autogenerate -m "descricao da mudanca"
alembic upgrade head
```

## Rotas

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/usuarios` | pública | Cadastra um usuário (`email`, `senha`) |
| POST | `/token` | pública | Login OAuth2 (form `username` = e-mail, `password`) → devolve o JWT |
| GET | `/tarefas` | pública | Lista tarefas (query opcional `?concluida=true/false`) |
| GET | `/tarefas/{tarefa_id}` | pública | Busca uma tarefa pelo id (path parameter) |
| POST | `/tarefas` | 🔒 JWT | Cria uma tarefa |
| PUT | `/tarefas/{tarefa_id}` | 🔒 JWT | Atualiza uma tarefa |
| DELETE | `/tarefas/{tarefa_id}` | 🔒 JWT | Remove uma tarefa |

Sem token (ou com token inválido/expirado) as rotas protegidas respondem `401 Unauthorized`.

Exemplo de corpo (POST/PUT):

```json
{ "titulo": "Leia as docs do FastAPI", "descricao": "Ler a documentação", "concluida": false }
```

## Autenticação

- A senha nunca é salva em texto puro: o Passlib gera o hash (`pbkdf2_sha256`) no cadastro e o verifica no login.
- O token é um JWT assinado com HS256, contém o e-mail em `sub` e expira em 30 minutos.
- A chave de assinatura vem da variável de ambiente `SECRET_KEY` (há um valor padrão só para desenvolvimento). Para gerar uma: `python -c "import secrets; print(secrets.token_hex(32))"`.

### Testando o login pelo Swagger

1. Abra http://127.0.0.1:8000/docs.
2. Em **POST /usuarios** → *Try it out*, envie `{"email": "ana@example.com", "senha": "segredo123"}`.
3. Clique no botão **Authorize** 🔓 (canto superior direito), preencha `username` = `ana@example.com` e `password` = `segredo123` e confirme. O Swagger chama `/token` e passa a enviar o header `Authorization: Bearer <token>` sozinho.
4. Agora POST/PUT/DELETE em `/tarefas` funcionam. Clique em **Logout** no mesmo botão e eles voltam a dar `401`.

### Testando pela linha de comando

```bash
curl -X POST http://127.0.0.1:8000/token -d "username=ana@example.com&password=segredo123"
# {"access_token":"eyJhbGciOi...","token_type":"bearer"}

curl -X POST http://127.0.0.1:8000/tarefas   -H "Authorization: Bearer <access_token>"   -H "Content-Type: application/json"   -d '{"titulo": "Estudar JWT"}'
```

Exemplo de token gerado pelo sistema (para `ana@example.com`, assinado com a chave padrão de desenvolvimento):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbmFAZXhhbXBsZS5jb20iLCJleHAiOjE3OTQyNjY5MDd9._TpIEqcNk5DHLoYqSHqvAaD1I86b2Egk59_ph4Aje9g
```

Decodificado (ex.: em https://jwt.io), o payload é `{"sub": "ana@example.com", "exp": 1794266907}`.

## Documentação (Swagger)

Cada rota tem `summary`, docstring (vira a descrição no Swagger), `tags`, descrição dos parâmetros e as respostas de erro documentadas (`401`, `404`, `409`) com o modelo `{"detail": "..."}`. Rotas protegidas aparecem com 🔒 no título.

## Testes

Os testes usam **Pytest** + **TestClient** (baseado no HTTPX) e rodam em um banco SQLite em memória, zerado a cada teste — o `tarefas.db` não é tocado.

```bash
pip install -r requirements.txt   # já inclui o pytest
pytest -v
```

| Teste | Verifica |
|-------|----------|
| `test_listar_tarefas_retorna_200` | `GET /tarefas` responde 200 com lista vazia |
| `test_tarefa_inexistente_retorna_404` | `GET /tarefas/999` responde 404 |
| `test_criar_sem_token_retorna_401` | `POST /tarefas` sem token é bloqueado (401) |
| `test_criar_com_token_invalido_retorna_401` | Token inválido é bloqueado (401) |
| `test_cadastro_duplicado_retorna_409` | E-mail repetido em `/usuarios` responde 409 |
| `test_login_com_senha_errada_retorna_401` | Login com senha errada responde 401 |
| `test_criar_tarefa_com_titulo_vazio_retorna_422` | Validação do Pydantic responde 422 |
| `test_crud_completo_com_token` | Cria, lê, atualiza, filtra e remove uma tarefa autenticado |
