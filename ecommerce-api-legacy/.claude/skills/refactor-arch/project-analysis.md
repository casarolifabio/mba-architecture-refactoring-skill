# Project Analysis — Heurísticas Agnósticas

Objetivo: descobrir a stack e a arquitetura **antes** de auditar. Não assuma Flask, Express ou qualquer framework pelo nome da pasta.

## 1. Linguagem

| Sinal | Conclusão |
|-------|-----------|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, `*.py` | Python |
| `package.json`, `*.js` / `*.ts`, `tsconfig.json` | JavaScript/TypeScript |
| `go.mod`, `*.go` | Go |
| `pom.xml`, `build.gradle`, `*.java` | Java |
| `Cargo.toml`, `*.rs` | Rust |
| `composer.json`, `*.php` | PHP |
| `Gemfile`, `*.rb` | Ruby |

Priorize **conteúdo** dos manifestos e imports sobre o nome do diretório.

## 2. Package manager

| Manifesto | Manager |
|-----------|---------|
| `requirements.txt` / `pyproject.toml` | pip / poetry / uv |
| `package.json` + `package-lock.json` | npm |
| `yarn.lock` | yarn |
| `pnpm-lock.yaml` | pnpm |
| `Pipfile.lock` | pipenv |

Liste dependências principais lendo o manifesto (não `node_modules`).

## 3. Framework web

### Python — inspecione imports

| Import / padrão | Framework |
|-----------------|-----------|
| `from flask import`, `Flask(__name__)` | Flask |
| `from fastapi import`, `APIRouter` | FastAPI |
| `django`, `urls.py`, `settings.py` | Django |
| `from litestar`, `from starlette` | Litestar/Starlette |

### Node — inspecione `package.json` + requires

| Dependência / padrão | Framework |
|----------------------|-----------|
| `express`, `app.get/post`, `Router()` | Express |
| `fastify` | Fastify |
| `@nestjs/core`, `NestFactory` | NestJS |
| `koa` | Koa |
| `hapi` | Hapi |

## 4. Banco de dados / ORM

Procure em imports, connection strings e config:

| Sinal | Conclusão |
|-------|-----------|
| `sqlite3`, `*.db`, `:memory:` | SQLite |
| `psycopg2`, `asyncpg`, `postgres://` | PostgreSQL |
| `mysql`, `pymysql`, `mysql2` | MySQL |
| `mongodb`, `mongoose` | MongoDB |
| `flask_sqlalchemy`, `SQLAlchemy` | SQLAlchemy ORM |
| `prisma`, `typeorm`, `sequelize`, `knex` | ORMs Node |
| `cursor.execute("SELECT...")` | SQL cru |
| `Model.query`, `db.session` | ORM ativo |

## 5. Domínio

Infira pelo vocabulário dominante em rotas, models e seeds:

- produtos, pedidos, carrinho, checkout → E-commerce
- courses, enrollments, payments, LMS → Educação / LMS
- tasks, users, categories, overdue → Task Manager
- invoices, ledger → Financeiro

Cite evidências (paths, nomes de tabelas).

## 6. Entry point

| Stack | Candidatos comuns |
|-------|-------------------|
| Python | `app.py`, `main.py`, `run.py`, `wsgi.py`, `if __name__ == "__main__"` |
| Node | `main` em `package.json`, `src/app.js`, `server.js`, `index.js` |

Confirme quem chama `app.run` / `listen` / `createServer`.

## 7. Rotas / endpoints

| Framework | Como encontrar |
|-----------|----------------|
| Flask | `@app.route`, `@bp.route`, `add_url_rule`, Blueprints |
| Express | `app.get/post/put/delete`, `router.*`, `app.use('/path', router)` |
| FastAPI | `@app.get`, `@router.post` |
| Django | `urlpatterns`, `path(`, `re_path(` |

Registre: método HTTP, path, handler.

## 8. Camadas

| Elemento | Sinais |
|----------|--------|
| Models | classes com schema/ORM, arquivos `models*`, queries SQL |
| Controllers | funções que orquestram request→model→response |
| Views/Routes | declaração de endpoints, serialização JSON |
| Services | classes/módulos de regras reutilizáveis |
| Config | `config`, `settings`, env vars, secrets |
| Middlewares | `app.use`, `@app.before_request`, error handlers |
| Testes | `tests/`, `*_test.py`, `*.test.js`, `*.spec.js` |

## 9. Classificação da arquitetura atual

| Nível | Descrição |
|-------|-----------|
| 0 — Monólito plano | 1–5 arquivos; rotas + SQL + regras misturados |
| 1 — God Class/Module | Uma classe/módulo concentra quase tudo |
| 2 — Camadas parciais | Pastas models/routes/services existem, mas responsabilidades vazam |
| 3 — MVC aproximado | Separação clara; restam smells pontuais |

## 10. Arquivos a ignorar

`node_modules/`, `venv/`, `.venv/`, `__pycache__/`, `.git/`, `dist/`, `build/`, `coverage/`, `*.pyc`, lockfiles (conteúdo), bancos binários.

## 11. Contagem

- Source files = arquivos de aplicação analisáveis (não docs da skill).
- Lines analyzed = soma aproximada das linhas lidas.

## 12. Template de saída Phase 1

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <...>
Framework:     <...>
Dependencies:  <principais>
Database:      <...>
Domain:        <...>
Architecture:  <nível + descrição>
Source files:  <N> files analyzed
Endpoints:     <lista resumida ou contagem + principais>
================================
```
