# Architecture Audit Report

> **Contexto temporal:** findings e números de linha abaixo referem-se ao **código legado pré-Phase 3**. Arquivos podem ter sido movidos/divididos/removidos na refatoração. Contagens históricas de findings foram preservadas.

## Project Information

Project: task-manager-api  
Language: Python  
Framework: Flask 3.0.0 (+ Flask-SQLAlchemy 3.1.1, flask-cors 4.0.0)  
Database: SQLite (`sqlite:///tasks.db`) via Flask-SQLAlchemy ORM  
Architecture: **Camadas parciais (nível 2)** — existem `models/`, `routes/`, `services/`, `utils/`, mas faltam `config/`, `controllers/` e middleware de erros; rotas acumulam validação, serialização, N+1 e regras; o service de notificação não é usado pelas rotas  
Entry point: `app.py`  
Files analyzed: 15 Python application files (excl. `.claude/`)  
Lines analyzed: ~969  

**Skill used:** `task-manager-api/.claude/skills/refactor-arch/` — hashes **idênticos** aos dos Projetos 1 e 2 (6/6 arquivos). Nenhuma regra específica de Task Manager foi adicionada.

**Skill portability: PASS**

## Executive Summary

CRITICAL: 3  
HIGH: 4  
MEDIUM: 3  
LOW: 2  
TOTAL: 12

## Existing Architecture Assessment

| Área | Classificação | Justificativa |
|------|---------------|---------------|
| **Models** | PARTIAL | Entidades SQLAlchemy claras (`User`, `Task`, `Category`) com `to_dict`/`is_overdue`; porém `User.to_dict` vaza senha e hash usa MD5. |
| **Routes** | POOR | Blueprints organizam paths, mas handlers concentram validação, persistência, overdue duplicado, N+1 e side-effects (`print`) — atuam como controllers gordos. |
| **Services** | POOR | Só `NotificationService`, com secrets SMTP hardcoded e estado em memória; **não é referenciado** pelas rotas (código morto operacional). |
| **Config** | POOR | `SECRET_KEY`, URI SQLite e `debug=True` hardcoded em `app.py`; `python-dotenv` está em `requirements.txt` mas não é usado. |
| **Error Handling** | POOR | `try/except` locais, `except:` bare (`task_routes.py:62`), sem `@app.errorhandler` central. |
| **Validation** | PARTIAL | Validações existem nas rotas (título, status, email regex); `utils/helpers.process_task_data` e `marshmallow` (dependência) **não são usados** — duplicação potencial. |
| **Dependency Boundaries** | PARTIAL | Models não importam Flask HTTP (bom); routes importam `db` + models diretamente; sem camada controller; service isolado e não integrado. |

## Findings

### [CRITICAL] Insecure Password Hashing — MD5

**File:** `models/user.py`  
**Lines:** 27-32  
**Anti-pattern:** Deprecated/Insecure Crypto (Security Issue)  
**Evidence:**
```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()
def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```
**Description:** MD5 sem salt para senhas — criptograficamente inadequado.  
**Impact:** Senhas recuperáveis por rainbow tables / força bruta rápida.  
**Recommendation:** `werkzeug.security.generate_password_hash` / bcrypt / argon2; rehash no login.

---

### [CRITICAL] Hardcoded SECRET_KEY

**File:** `app.py`  
**Lines:** 13  
**Anti-pattern:** Hardcoded Credentials / Secrets  
**Evidence:** `app.config['SECRET_KEY'] = '***REDACTED***'`

> O valor original presente no código legado foi redigido neste relatório por segurança. O finding foi identificado antes da refatoração.  
**Description:** Segredo de aplicação fixo no código-fonte.  
**Impact:** Sessões/assinaturas previsíveis se o código vazar.  
**Recommendation:** `os.environ` + módulo `config/`; usar `python-dotenv` já declarado.

---

### [CRITICAL] Hardcoded SMTP Credentials

**File:** `services/notification_service.py`  
**Lines:** 7-10  
**Anti-pattern:** Hardcoded Credentials / Secrets  
**Evidence:** `email_user = '***REDACTED***'`, `email_password = '***REDACTED***'` (+ host/port fixos).

> O valor original presente no código legado foi redigido neste relatório por segurança. O finding foi identificado antes da refatoração.  
**Description:** Credenciais de e-mail embutidas no service.  
**Impact:** Comprometimento da conta SMTP se o repositório vazar (mesmo com service atualmente não wired às rotas).  
**Recommendation:** Env vars; não commitar senhas.

---

### [HIGH] Password Hash Exposed in Serialization

**File:** `models/user.py`  
**Lines:** 16-25  
**Anti-pattern:** Missing Input Validation / insecure serialization (Security Issue)  
**Evidence:** `'password': self.password` em `to_dict()`; usado em `user_routes.py` create/update/login/get (`user_routes.py:33`, `85-86`, `129`, `209`).  
**Description:** API devolve o hash MD5 ao cliente.  
**Impact:** Facilita offline cracking; vazamento direto de segredo de autenticação.  
**Recommendation:** Remover `password` de qualquer serialização pública.

---

### [HIGH] Business Logic in Routes

**File:** `routes/task_routes.py`  
**Lines:** 11-63, 85-154  
**Anti-pattern:** Business Logic in Routes/Controllers  
**Evidence:** `GET /tasks` monta dict manual, calcula overdue e busca User/Category por id; `POST /tasks` valida campos, regras de status/priority e persiste — ~70 linhas sem controller/service.  
**Description:** Camada HTTP assume papel de application service.  
**Impact:** Rotas difíceis de testar; MVC apenas nominal.  
**Recommendation:** Extrair controllers + reutilizar `Task.is_overdue()` / `to_dict()`; validators dedicados.

---

### [HIGH] Fake JWT Token (Weak Auth)

**File:** `routes/user_routes.py`  
**Lines:** 207-210  
**Anti-pattern:** Tight Coupling / Missing Dependency Boundaries (auth falsa)  
**Evidence:** `'token': 'fake-jwt-token-' + str(user.id)` (padrão previsível; valor ilustrativo redigido conceitualmente)

> O valor original presente no código legado foi redigido neste relatório por segurança. O finding foi identificado antes da refatoração.  
**Description:** Token previsível sem assinatura; não há middleware que valide JWT real.  
**Impact:** Qualquer cliente forja `fake-jwt-token-<id>` e simula autenticação.  
**Recommendation:** JWT assinado (PyJWT) com `SECRET_KEY` de env, ou remover token até implementar auth de verdade.

---

### [HIGH] N+1 Queries on Task Listing

**File:** `routes/task_routes.py`  
**Lines:** 41-57  
**Anti-pattern:** N+1 Query  
**Evidence:** Para cada task: `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` dentro do loop.  
**Description:** 1 + 2N queries na listagem.  
**Impact:** Latência proporcional ao número de tasks.  
**Recommendation:** `joinedload` / selectinload nos relationships já declarados no model.

---

### [MEDIUM] Duplicated `is_overdue` Logic

**Files / Lines:**  
- `routes/task_routes.py:30-39`, `71-80`  
- `routes/user_routes.py:171-180`  
- `routes/report_routes.py:33-43`  
**Anti-pattern:** Duplicated Code  
**Evidence:** Árvore idêntica de `if due_date < datetime.utcnow()` repetida; o model já expõe `Task.is_overdue()` em `models/task.py:50-60`, mas as rotas não o usam.  
**Description:** Violação DRY com risco de drift.  
**Impact:** Correção de regra de atraso exige N edições.  
**Recommendation:** Chamar `task.is_overdue()` (e alinhar timezone).

---

### [MEDIUM] Inconsistent / Bare Error Handling

**File:** `routes/task_routes.py`  
**Lines:** 62-63, 137-138, 225-238 (padrão similar em `user_routes`/`report_routes`)  
**Anti-pattern:** Inconsistent Error Handling  
**Evidence:** `except:` bare engole qualquer erro e retorna 500 genérico; outros pontos usam `except Exception`; sem errorhandler Flask.  
**Description:** Tratamento fragmentado e opaco.  
**Impact:** Bugs silenciosos; respostas inconsistentes.  
**Recommendation:** Middleware/`@app.errorhandler` + exceções tipadas.

---

### [MEDIUM] Missing Central Config + Unused dotenv/marshmallow

**File:** `app.py`  
**Lines:** 11-13, 34  
**Anti-pattern:** Tight Coupling / Hardcoded config  
**Evidence:** URI, `SECRET_KEY` e `app.run(debug=True)` no entry point; `python-dotenv` e `marshmallow` em `requirements.txt` sem uso no código de rotas/models.  
**Description:** Configuração não externalizada; dependências declaradas ociosas.  
**Impact:** Ambiente/prod indiferenciados; dívida de stack.  
**Recommendation:** `config/settings.py` + dotenv; usar marshmallow ou remover se YAGNI.

---

### [LOW] Fragile Type Check `type(x) == list`

**File:** `routes/task_routes.py`  
**Lines:** 141  
**Anti-pattern:** Magic Numbers / Poor Naming (estilo / code smell)  
**Evidence:** `if type(tags) == list:` (também `helpers.py:103`, `task_routes` update ~210).  
**Description:** Comparação de tipo frágil vs `isinstance`.  
**Impact:** Falha com subclasses de list; estilo não idiomático.  
**Recommendation:** `isinstance(tags, list)`.

---

### [LOW] Confirmed Deprecated API — `datetime.utcnow()`

**Files:** `models/user.py:14`, `models/task.py:15-16,52`, `models/category.py:11`, `routes/task_routes.py:31,72,215`, `routes/user_routes.py:172`, `routes/report_routes.py:35,42,45,71`, `services/notification_service.py:35`, `utils/helpers.py:38`, `seed.py` (múltiplos)  
**Anti-pattern:** Deprecated APIs  
**Evidence:** Uso disseminado de `datetime.utcnow()` — **deprecated since Python 3.12** (docs CPython).  
**Description:** API oficialmente marcada para remoção futura.  
**Impact:** Warnings em 3.12+; quebra eventual.  
**Recommendation:** `datetime.now(timezone.utc)`.

## Manual Analysis Coverage

Manual findings no README: **8**

| ID Manual | Detectado? |
|-----------|------------|
| P3-C1 MD5 | MATCH |
| P3-H1 to_dict password | MATCH |
| P3-H2 logic in routes | MATCH |
| P3-H3 fake JWT | MATCH |
| P3-M1 SMTP hardcoded | MATCH (severidade elevada a CRITICAL pelo catálogo de secrets) |
| P3-M2 overdue duplicado | MATCH |
| P3-L1 type==list | MATCH |
| P3-L2 utcnow | MATCH |

**Detected automatically: 8/8**  
**Coverage: 100%**

### NEW FINDINGS (além do manual)

- SECRET_KEY hardcoded (`app.py:13`) — CRITICAL  
- N+1 em `GET /tasks` — HIGH  
- Error handling bare/inconsistente — MEDIUM  
- Config central ausente + deps ociosas — MEDIUM  

### Divergências

- SMTP: manual MEDIUM; Skill CRITICAL (catálogo unifica secrets hardcoded). Justificativa: senha SMTP no fonte é secret independente de severidade “de negócio”.

## Deprecated API Assessment

### Confirmed Deprecated API

| Item | Evidência | Ação |
|------|-----------|------|
| `datetime.utcnow()` | Python 3.12+ docs | `datetime.now(timezone.utc)` |
| `Model.query.get()` (legado SQLAlchemy 2.x) | Usado em rotas (`User.query.get`, `Task.query.get`, …) | `db.session.get(Model, id)` |

### Security Issues (não são “deprecated APIs”)

| Item | Local |
|------|-------|
| MD5 para senha | `models/user.py:27-32` |
| Hash na resposta JSON | `models/user.py:21` |
| SECRET_KEY / SMTP hardcoded | `app.py:13`, `notification_service.py:9-10` |
| Token fake | `user_routes.py:210` |

### Code Smells

| Item | Local |
|------|-------|
| Business logic nas routes | `task_routes.py` |
| Overdue duplicado | várias routes |
| `type(x) == list` | `task_routes.py:141` |
| `print` como log | rotas / service |
| bare `except:` | `task_routes.py:62` |

### Technical Debt

| Item | Nota |
|------|------|
| `marshmallow` / `python-dotenv` / `requests` no requirements sem uso aparente nas rotas | Dependências ociosas |
| `NotificationService` não wired | Service morto com secrets |
| `helpers.process_task_data` não usado pelas routes | Validação duplicada potencial |
| `app.run(debug=True)` hardcoded | Default inseguro para qualquer deploy |

## Recommended Target Architecture

Incremental — **preservar** `models/`, `routes/`, `services/`, `utils/`; não recriar árvore por vaidade:

```text
task-manager-api/
├── app.py                    # composition root fino
├── config/settings.py        # NOVO — env/secrets/URI/DEBUG
├── database.py               # manter
├── models/                   # manter; corrigir User hash + to_dict
├── controllers/              # NOVO — extrair de routes gordas
├── routes/                   # manter blueprints finos
├── services/                 # corrigir notification; wire ou remover
├── middlewares/              # NOVO — error handlers
├── validators/               # NOVO ou ativar helpers/marshmallow
├── utils/helpers.py          # limpar dead code / isinstance
└── seed.py
```

## Validation Plan

1. Inventário de endpoints (22 rotas abaixo)
2. `pip install -r requirements.txt`
3. `python seed.py` then `python app.py`
4. Smoke: `/health`, `/tasks`, `/users`, `/login`, `/reports/summary`, `/categories`
5. Confirmar ausência de `password` nas respostas e hash forte
6. Não remover endpoints

### Inventário de endpoints (baseline)

| Método | Path |
|--------|------|
| GET | `/` |
| GET | `/health` |
| GET/POST | `/tasks` |
| GET/PUT/DELETE | `/tasks/<task_id>` |
| GET | `/tasks/search` |
| GET | `/tasks/stats` |
| GET/POST | `/users` |
| GET/PUT/DELETE | `/users/<user_id>` |
| GET | `/users/<user_id>/tasks` |
| POST | `/login` |
| GET | `/reports/summary` |
| GET | `/reports/user/<user_id>` |
| GET/POST | `/categories` |
| PUT/DELETE | `/categories/<cat_id>` |

**Total: 22 endpoints** (contando métodos distintos por path)

---

**Phase 2 status:** COMPLETE  
**Phase 3 status:** COMPLETE (autorizada com `y`)

---

## Refactoring Results

### Arquitetura antes

```text
app.py, database.py, seed.py
models/   routes/   services/   utils/
(sem config/controllers/middlewares/validators)
```

### Arquitetura depois (incremental)

```text
task-manager-api/
├── app.py
├── config/settings.py + .env.example
├── database.py
├── models/          # preservado + corrigido
├── routes/          # preservado — handlers finos
├── controllers/     # NOVO
├── services/        # NotificationService wired + config
├── validators/      # NOVO
├── middlewares/     # NOVO error handlers
├── utils/           # helpers + timeutils + tokens
└── seed.py
```

### Decisões arquiteturais

1. **Não reescreveu** models/routes/services/utils do zero — extraiu controllers e afilou routes.
2. **`NotificationService`**: integrado em `create_task` quando há `user_id`; SMTP só envia se `SMTP_ENABLED=true` (default false) — evita código morto e secrets no fonte.
3. **Token de login**: campo `token` preservado; implementação passou de string fake para **itsdangerous** (assinado). **Não é JWT** — documentado honestamente; formato do valor mudou por segurança.
4. **SQLite + SQLAlchemy** mantidos; `utc_now()` naive UTC para compatibilidade com colunas existentes.

### Reauditoria dos 12 findings

| Finding | Status |
|---------|--------|
| MD5 password hash | **FIXED** — Werkzeug |
| SECRET_KEY hardcoded | **FIXED** — env/config |
| SMTP hardcoded | **FIXED** — env; default desabilitado |
| password em `to_dict` | **FIXED** |
| Business logic nas routes | **FIXED** — controllers |
| Fake JWT | **FIXED** (insegurança); token assinado itsdangerous — não JWT |
| N+1 listagem tasks | **FIXED** — `joinedload` |
| overdue duplicado | **FIXED** — `Task.is_overdue()` |
| bare except / erros | **FIXED** — middleware |
| config ausente | **FIXED** |
| `type(x)==list` | **FIXED** — `isinstance` |
| `datetime.utcnow` | **FIXED** — `utc_now()` |
| `Model.query.get` | **FIXED** — `db.session.get` |

**Fixed: 12 | Partially fixed: 0 | Remaining: 0** (dívida menor: `marshmallow` ainda ocioso no requirements — fora dos 12 findings formais)

### Validações executadas

```bash
pip install -r requirements.txt
python -c "from app import app; ..."   # IMPORT_OK, 22 routes
python seed.py
python app.py
python scripts/smoke_test.py           # 26 passed / 0 failed
rg hashlib.md5 / utcnow / query.get / fake-jwt / secrets
```

Resultados reais:

- Boot: PASS  
- Smoke: 26/26 PASS (CRUD tasks/users, login 200/401, categories, reports, search, stats, health, 400/404)  
- Automated tests: 0/0 (nenhum existia)  
- Password ausente nas responses: PASS  
- MD5 / utcnow / query.get / fake-jwt / secrets hardcoded: ausentes no código de aplicação  
