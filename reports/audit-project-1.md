# Architecture Audit Report

> **Contexto temporal:** findings e números de linha abaixo referem-se ao **código legado pré-Phase 3**. Arquivos podem ter sido movidos/divididos/removidos na refatoração. Contagens históricas de findings foram preservadas.

## Project Information

Project: code-smells-project  
Language: Python  
Framework: Flask 3.1.1 (+ flask-cors 5.0.1)  
Database: SQLite (`loja.db`) via módulo `sqlite3` (SQL cru, sem ORM)  
Architecture: Monólito plano — 4 arquivos de aplicação (`app.py`, `controllers.py`, `models.py`, `database.py`); rotas registradas no entry point; controllers com HTTP + validação; models com SQL e regras de múltiplos domínios  
Files analyzed: 4 source files (+ `requirements.txt`, `README.md`)  
Lines analyzed: ~780 (app.py 89 + controllers.py 293 + models.py 315 + database.py 87)

## Executive Summary

CRITICAL: 4  
HIGH: 3  
MEDIUM: 3  
LOW: 3  
TOTAL: 13

## Findings

### [CRITICAL] SQL Injection / Unsafe Query Construction

**File:** `models.py`  
**Lines:** 28-297  
**Evidence:** Queries montadas por concatenação, por exemplo:
- L28: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))`
- L47-50: `INSERT INTO produtos ... VALUES ('" + nome + "', '" + descricao + "'...`
- L109-111: `WHERE email = '" + email + "' AND senha = '" + senha + "'`
- L289-297: `buscar_produtos` concatena `termo`, `categoria`, `preco_min`, `preco_max` na string SQL  
**Description:** Entrada do cliente e parâmetros de aplicação são interpolados diretamente no SQL, sem placeholders.  
**Impact:** Atacante pode ler/alterar/apagar dados (produtos, usuários, pedidos) via busca, login, criação de produto, etc.  
**Recommendation:** Usar `cursor.execute(sql, params)` com `?` placeholders em todas as queries; validar tipos; nunca montar SQL com `+` ou f-strings a partir de input.

---

### [CRITICAL] Arbitrary SQL Execution Endpoint

**File:** `app.py`  
**Lines:** 59-78  
**Evidence:** `POST /admin/query` lê `dados.get("sql")` e executa `cursor.execute(query)` sem autenticação; commits em statements não-SELECT.  
**Description:** Backdoor administrativo que permite SQL arbitrário pelo corpo JSON.  
**Impact:** Comprometimento total do banco por qualquer cliente que alcance a porta.  
**Recommendation:** Remover o endpoint em produção ou proteger com auth forte + allowlist de statements; preferir operações de domínio tipadas.

---

### [CRITICAL] Hardcoded Credentials / Secrets

**File:** `app.py`  
**Lines:** 7-8  
**Evidence:** `app.config["SECRET_KEY"] = "***REDACTED***"` e `app.config["DEBUG"] = True`. Também `app.run(..., debug=True)` em L88. Seeds com senhas de demonstração em texto puro em `database.py:76-78` (valores redigidos).

> O valor original presente no código legado foi redigido neste relatório por segurança. O finding foi identificado antes da refatoração.  
**Description:** Segredo de aplicação e modo debug fixos no código-fonte.  
**Impact:** Sessões/assinaturas previsíveis; superfície de debug exposta se o serviço for publicado.  
**Recommendation:** Ler `SECRET_KEY` e `DEBUG` de variáveis de ambiente via módulo `config`; nunca commitar secrets reais; hashear senhas de seed.

---

### [CRITICAL] Plaintext Passwords Exposed in API Responses

**File:** `models.py`  
**Lines:** 72-103  
**Evidence:** `get_todos_usuarios` e `get_usuario_por_id` incluem `"senha": row["senha"]` no dict retornado; senhas armazenadas em texto puro (`database.py` seed; `criar_usuario` L126-129 insere senha sem hash).  
**Description:** Credenciais em claro na persistência e na serialização.  
**Impact:** Qualquer chamada a `GET /usuarios` ou `GET /usuarios/<id>` vaza senhas.  
**Recommendation:** Hash (werkzeug/bcrypt); nunca retornar campo senha; login por comparação de hash.

---

### [HIGH] God Module — Multi-Domain Persistence and Business Rules

**File:** `models.py`  
**Lines:** 1-315  
**Evidence:** Mesmo arquivo define operações de produtos (L4-70, 285-314), usuários (L72-131), pedidos/itens (L133-233, 275-283) e relatório de vendas (L235-273).  
**Description:** Violação extrema de Single Responsibility / MVC Model cohesion.  
**Impact:** Mudanças locais geram regressões cruzadas; testes unitários inviáveis.  
**Recommendation:** Separar `produto_model`, `usuario_model`, `pedido_model` e serviço/relatório; controllers por domínio.

---

### [HIGH] Secret Leak via Public Health Endpoint

**File:** `controllers.py`  
**Lines:** 264-290  
**Evidence:** Resposta de `health_check` inclui `"secret_key": "***REDACTED***"`, `"debug": True`, `"ambiente": "producao"`.

> O valor original presente no código legado foi redigido neste relatório por segurança. O finding foi identificado antes da refatoração.  
**Description:** Endpoint de saúde funciona como oráculo de configuração sensível.  
**Impact:** Qualquer cliente obtém a SECRET_KEY sem autenticação.  
**Recommendation:** Health deve retornar apenas status/conectividade; remover secrets do payload.

---

### [HIGH] Global Mutable Database Connection

**File:** `database.py`  
**Lines:** 4-11  
**Evidence:** `db_connection = None` no módulo; `get_db()` usa `global db_connection` e reutiliza uma conexão `check_same_thread=False` para toda a aplicação.  
**Description:** Estado global mutável acopla todo o código à conexão singleton.  
**Impact:** Dificulta testes, lifecycle e segurança de concorrência; schema/seed misturados ao getter.  
**Recommendation:** Conexão por request (`flask.g`) ou pool; separar migrations/seed do getter.

---

### [MEDIUM] N+1 Queries on Order Listings

**File:** `models.py`  
**Lines:** 171-233  
**Evidence:** Em `get_pedidos_usuario` e `get_todos_pedidos`, para cada pedido executa `SELECT * FROM itens_pedido WHERE pedido_id = ...` e, para cada item, `SELECT nome FROM produtos WHERE id = ...` (L187-199, L219-231).  
**Description:** Padrão N+1 (na prática N×M queries).  
**Impact:** Latência cresce com pedidos × itens.  
**Recommendation:** JOIN único (pedidos + itens + produtos) e agrupamento em memória.

---

### [MEDIUM] Duplicated Product Validation

**File:** `controllers.py`  
**Lines:** 24-54 e 64-90  
**Evidence:** `criar_produto` e `atualizar_produto` repetem checagens de presença de campos, preço/estoque negativos e (em create) tamanho do nome/categoria.  
**Description:** Violação DRY; regras podem divergir (PUT não revalida tamanho do nome/categoria da mesma forma).  
**Impact:** Bugs de inconsistência entre create e update.  
**Recommendation:** Extrair `validate_produto_payload(dados)` compartilhado.

---

### [MEDIUM] Inconsistent / Scattered Error Handling

**File:** `controllers.py`  
**Lines:** 5-292  
**Evidence:** Quase cada handler repete `try/except Exception` retornando `{"erro": str(e)}` com 500; não há errorhandler Flask central; `app.py` admin routes tratam erros de forma distinta.  
**Description:** Tratamento de erro duplicado e inconsistente entre camadas.  
**Impact:** Vazamento de detalhes internos; manutenção custosa.  
**Recommendation:** Middleware/`@app.errorhandler` + exceções de domínio tipadas.

---

### [LOW] Magic Numbers in Sales Discount Rules

**File:** `models.py`  
**Lines:** 256-262  
**Evidence:** Limiares `10000`, `5000`, `1000` e taxas `0.1`, `0.05`, `0.02` literais em `relatorio_vendas`.  
**Description:** Regras de negócio opacas.  
**Impact:** Alteração de política comercial exige caçar literais.  
**Recommendation:** Constantes nomeadas em config/domínio (`DISCOUNT_TIERS`).

---

### [LOW] print() Used as Application Logging

**File:** `controllers.py`  
**Lines:** 8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248-250  
**Evidence:** Mensagens de listagem, criação, login, “ENVIANDO EMAIL/SMS/PUSH” via `print`.  
**Description:** Observabilidade inadequada; side-effects simulados como log.  
**Impact:** Impossível filtrar níveis ou correlacionar requests.  
**Recommendation:** Módulo `logging`; notificações em service dedicado.

---

### [LOW] Deprecated / Unsafe Debug Defaults (API Hygiene)

**File:** `app.py`  
**Lines:** 8, 88  
**Evidence:** `DEBUG = True` hardcoded e `app.run(..., debug=True)` — padrão inadequado para qualquer ambiente além de lab local.  
**Description:** API de desenvolvimento deixada como default permanente (catálogo: Deprecated/Unsafe defaults).  
**Impact:** Werkzeug debugger e stack traces se expostos.  
**Recommendation:** `debug` apenas via env; default `False`.

## Architecture Assessment

O projeto é um monólito plano de e-commerce. Há uma separação nominal `app` / `controllers` / `models` / `database`, mas:

- `models.py` é um God Module multi-domínio com SQL inseguro;
- `controllers.py` mistura HTTP, validação e side-effects;
- `app.py` registra rotas e ainda implementa endpoints admin perigosos;
- `database.py` mantém conexão global e faz DDL+seed no getter.

Não há config externa, middlewares de erro/auth, nem camada de validação reutilizável. A superfície de ataque (SQLi + SQL admin + secret no health + senhas em claro) é crítica.

## Recommended Target Architecture

```text
code-smells-project/
├── app.py                      # composition root
├── config/
│   └── settings.py             # SECRET_KEY, DEBUG, DB_PATH via env
├── models/
│   ├── produto_model.py
│   ├── usuario_model.py
│   └── pedido_model.py
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   └── health_controller.py
├── views/
│   └── routes.py               # declaração HTTP → controllers
├── middlewares/
│   └── error_handler.py
├── validators/
│   └── produto_validator.py
├── database.py                 # conexão por request / init schema
└── requirements.txt
```

## Validation Plan

1. Inventário de endpoints atuais (ver abaixo)
2. `pip install -r requirements.txt`
3. `python app.py` — verificar boot em `:5000`
4. Smoke: `GET /health`, `GET /produtos`, `POST /login`, `GET /pedidos`, etc.
5. Confirmar que contratos JSON (`sucesso`, `dados`, status codes) permanecem
6. Garantir ausência de SQL concat e de secret no health

### Inventário de endpoints (baseline pré-refatoração)

| Método | Path | Notas |
|--------|------|-------|
| GET | `/` | índice |
| GET | `/health` | health (hoje vaza secret) |
| GET | `/produtos` | lista |
| GET | `/produtos/busca` | query `q`, `categoria`, `preco_min`, `preco_max` |
| GET | `/produtos/<id>` | detalhe |
| POST | `/produtos` | cria |
| PUT | `/produtos/<id>` | atualiza |
| DELETE | `/produtos/<id>` | remove |
| GET | `/usuarios` | lista (hoje com senha) |
| GET | `/usuarios/<id>` | detalhe |
| POST | `/usuarios` | cria |
| POST | `/login` | body email/senha |
| POST | `/pedidos` | cria pedido |
| GET | `/pedidos` | lista todos |
| GET | `/pedidos/usuario/<usuario_id>` | por usuário |
| PUT | `/pedidos/<pedido_id>/status` | status |
| GET | `/relatorios/vendas` | relatório |
| POST | `/admin/reset-db` | reset |
| POST | `/admin/query` | SQL livre |

## Deprecated APIs Reviewed

| API | Local | Severidade | Ação |
|-----|-------|------------|------|
| `DEBUG=True` / `app.run(debug=True)` hardcoded | `app.py:8,88` | LOW (contexto) / HIGH se exposto | Controlar via env; default False |
| Senhas em texto puro (padrão inseguro equivalente a “deprecated crypto”) | `models.py` + seed | CRITICAL | Hash + omitir na serialização |
| Concat SQL (padrão inseguro) | `models.py` | CRITICAL | Prepared statements |

---

**Phase 2 status:** COMPLETE  
**Phase 3 status:** COMPLETE (autorizada pelo usuário com `y`)

---

## Refactoring Results

### Estrutura anterior

```text
code-smells-project/
├── app.py
├── controllers.py
├── models.py
├── database.py
└── requirements.txt
```

### Estrutura nova

```text
code-smells-project/
├── app.py                      # composition root (create_app)
├── database.py                 # conexão via flask.g + schema/seed
├── requirements.txt
├── config/
│   ├── __init__.py
│   └── settings.py             # SECRET_KEY/DEBUG/DB via env
├── models/
│   ├── __init__.py
│   ├── produto_model.py
│   ├── usuario_model.py
│   └── pedido_model.py
├── controllers/
│   ├── __init__.py
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   ├── health_controller.py
│   └── admin_controller.py
├── views/
│   ├── __init__.py
│   └── routes.py
├── middlewares/
│   ├── __init__.py
│   └── error_handler.py
└── validators/
    ├── __init__.py
    └── produto_validator.py
```

### Arquivos criados / movidos / removidos

| Ação | Path |
|------|------|
| Criado | `config/settings.py`, `config/__init__.py` |
| Criado | `models/produto_model.py`, `usuario_model.py`, `pedido_model.py`, `__init__.py` |
| Criado | `controllers/*.py` (5 controllers + `__init__.py`) |
| Criado | `views/routes.py`, `views/__init__.py` |
| Criado | `middlewares/error_handler.py` |
| Criado | `validators/produto_validator.py` |
| Reescrito | `app.py`, `database.py`, `README.md` |
| Removido | `models.py`, `controllers.py` (legado monolítico) |

### Findings corrigidos

| Finding Phase 2 | Status |
|-----------------|--------|
| SQL Injection (concat) | CORRIGIDO — queries com `?` placeholders |
| Hardcoded SECRET_KEY / DEBUG | CORRIGIDO — `config/settings.py` + env (default DEBUG=false) |
| Senhas em texto puro + exposição | CORRIGIDO — `werkzeug` hash; respostas sem campo `senha` |
| God Module `models.py` | CORRIGIDO — models por domínio |
| Secret no `/health` | CORRIGIDO — payload sem `secret_key` |
| Conexão global mutável | CORRIGIDO — `flask.g` + teardown |
| N+1 pedidos | CORRIGIDO — JOIN + agrupamento |
| Validação duplicada produto | CORRIGIDO — `validate_produto_payload` no POST |
| Error handling espalhado | CORRIGIDO — `register_error_handlers` |
| Magic numbers desconto | CORRIGIDO — constantes em `settings` |
| `print()` como log | CORRIGIDO — `logging` |
| Debug hardcoded | CORRIGIDO — via env |
| Endpoint `/admin/query` SQL livre | **RESTANTE** — endpoint preservado por contrato (19 endpoints) |

**Fixed: 12 | Remaining: 1** (risco residual consciente em `/admin/query`)

### Validações executadas

Comandos:

```bash
pip install -r requirements.txt
python -c "from app import app; ..."   # IMPORT_OK, 19 endpoints
FLASK_SKIP_DOTENV=1 python app.py      # boot
python scripts/smoke_test.py           # smoke HTTP (21 passed / 0 failed)
python _db_check.py                    # SQLite + reset-db
```

Resultados reais:

- **Import:** `IMPORT_OK app` — 19 rotas registradas (sem static)
- **Boot:** PASS — `Running on http://127.0.0.1:5000` (sem Traceback após `load_dotenv=False`)
- **Smoke tests:** 21 passed / 0 failed (inclui GET/POST/PUT/DELETE, login 200/401, 404, busca com payload tipo injection)
- **Endpoint `/admin/reset-db`:** PASS (200) — validado em `_db_check.py`
- **Cobertura de endpoints:** 19/19 paths preservados
- **Automated tests:** nenhum arquivo de teste existia no projeto — 0 passed / 0 failed (N/A)
- **Database:** PASS — tabelas OK; senha seed com prefixo `scrypt:`; após reset counts=0; health sem `secret_key`
- **Usuários API:** chaves `criado_em, email, id, nome, tipo` (sem `senha`)

### Problemas restantes

1. `POST /admin/query` continua executando SQL arbitrário (requisito de preservar o endpoint). Mitigação futura: auth + allowlist, sem remover a rota.
2. Boot no Windows falhou inicialmente ao carregar um `.env` inválido no ambiente do usuário; contornado com `load_dotenv=False` no `app.run`.

### Comparação objetiva

| | ANTES | DEPOIS |
|--|------:|-------:|
| Endpoints | 19 | 19 preservados |
| CRITICAL | 4 | 1 residual (`/admin/query`) |
| HIGH | 3 | 0 |
| MEDIUM | 3 | 0 |
| LOW | 3 | 0 |
| Boot | legado | PASS |
| Smoke | — | 21/21 PASS |
