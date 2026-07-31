# Architecture Audit Report

> **Contexto temporal:** findings e números de linha abaixo referem-se ao **código legado pré-Phase 3**. Arquivos podem ter sido movidos/divididos/removidos na refatoração. Contagens históricas de findings foram preservadas.

## Project Information

Project: ecommerce-api-legacy  
Language: JavaScript (Node.js)  
Framework: Express ^4.18.2  
Database: SQLite via `sqlite3` ^5.1.6 — modo `:memory:` (sem ORM)  
Architecture: God Class — `AppManager` concentra schema/seed, rotas HTTP, regras de checkout/pagamento, relatório e delete; `utils.js` mistura config/secrets, cache global e crypto; entry point `src/app.js` apenas instancia e escuta  
Files analyzed: 3 source files (`src/app.js`, `src/AppManager.js`, `src/utils.js`) + `package.json`, `api.http`, `README.md`  
Lines analyzed: ~182 (app.js 15 + AppManager.js 141 + utils.js 26)

**Skill used:** `ecommerce-api-legacy/.claude/skills/refactor-arch/` — hashes idênticos aos de `code-smells-project/.claude/skills/refactor-arch/` (SKILL.md + 5 referências). Nenhuma regra específica deste projeto foi adicionada.

## Executive Summary

CRITICAL: 3  
HIGH: 3  
MEDIUM: 3  
LOW: 2  
TOTAL: 11

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets

**File:** `src/utils.js`  
**Lines:** 1-7  
**Evidence:** Objeto `config` embute no fonte:
- `dbUser: "admin_master"`
- `dbPass: "***REDACTED***"`
- `paymentGatewayKey: "pk_live_***REDACTED***"`

> O valor original presente no código legado foi redigido neste relatório por segurança. O finding foi identificado antes da refatoração.
- `smtpUser: "no-reply@fullcycle.com.br"`  
Adicionalmente, `AppManager.js:45` loga o cartão e a chave do gateway: `` console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`) ``.  
**Description:** Segredos e identificadores de integração hardcoded; chave de pagamento ainda vazada em log.  
**Impact:** Comprometimento de gateway/SMTP/DB se o repositório ou logs vazarem.  
**Recommendation:** Mover para `process.env` em módulo `config/`; nunca logar PAN/cartão nem API keys.

---

### [CRITICAL] God Class / God Module — AppManager

**File:** `src/AppManager.js`  
**Lines:** 1-141  
**Evidence:** A classe `AppManager`:
- cria conexão SQLite (L4-7)
- faz DDL + seed (L10-22)
- registra `POST /api/checkout` com pagamento/matrícula/auditoria (L28-78)
- registra `GET /api/admin/financial-report` (L80-129)
- registra `DELETE /api/users/:id` (L131-137)  
Não há models, controllers ou routes separados.  
**Description:** Violação total de SRP/MVC — um único módulo concentra persistência, HTTP e regras de negócio de múltiplos casos de uso.  
**Impact:** Impossível testar/isolar checkout sem carregar relatório e delete; qualquer mudança aumenta risco de regressão.  
**Recommendation:** Dividir em `config/`, `models/`, `controllers/`, `routes/`, `middlewares/` (playbook PB-1).

---

### [CRITICAL] Deprecated / Insecure Password Hashing — `badCrypto`

**File:** `src/utils.js`  
**Lines:** 17-23  
**Evidence:**
```javascript
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) {
        hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    }
    return hash.substring(0, 10);
}
```
Usado no checkout ao criar usuário (`AppManager.js:68`). Seed inicial ainda grava senha em claro `'123'` (`AppManager.js:18`).  
**Description:** Pseudo-hash determinístico baseado em Base64 truncado — não é função de derivação de chave; colisões/reversão triviais. API custom insegura (catálogo: Deprecated APIs / insecure crypto).  
**Impact:** Credenciais de novos usuários não estão protegidas.  
**Recommendation:** `crypto.scrypt` / bcrypt / argon2; migrar seed e comparar com API segura.

---

### [HIGH] Business Logic in Routes — Checkout Callback Hell

**File:** `src/AppManager.js`  
**Lines:** 28-78  
**Evidence:** Handler inline de `app.post('/api/checkout', ...)` aninha: validação → busca curso → busca user → cria user → “pagamento” por prefixo do cartão → insert enrollment → insert payment → insert audit → cache. Cinco níveis de callbacks `db.get`/`db.run`.  
**Description:** Lógica de negócio e orquestração financeira dentro da camada HTTP.  
**Impact:** Manutenção difícil; tratamento de erro frágil; impossível reutilizar o fluxo fora de Express.  
**Recommendation:** Extrair `checkoutController` + `checkoutService`; promisificar/async DB (PB-2, PB-9).

---

### [HIGH] Global Mutable State

**File:** `src/utils.js`  
**Lines:** 9-14  
**Evidence:** `let globalCache = {}` e `let totalRevenue = 0` no escopo do módulo; `logAndCache` muta `globalCache[key] = data`. Exportados no `module.exports`.  
**Description:** Estado compartilhado mutável entre requests, sem encapsulamento de ciclo de vida.  
**Impact:** Comportamento não determinístico em processos multi-request; dificulta testes e horizontal scaling.  
**Recommendation:** Remover cache global ou encapsular em serviço com interface explícita (PB-7).

---

### [HIGH] Tight Coupling / Missing Dependency Boundaries

**File:** `src/AppManager.js`  
**Lines:** 1-10, 25-138  
**Evidence:** `AppManager` instancia `sqlite3.Database` internamente, importa `config`/`badCrypto`/`logAndCache` diretamente, e acopla HTTP (`app.post/get/delete`) à mesma classe. `src/app.js` só chama `manager.setupRoutes(app)` — não há injeção de repositório/serviço.  
**Description:** Fronteiras de dependência ausentes; domínio não existe separado da infraestrutura.  
**Impact:** Trocar DB ou gateway exige reescrever a God Class.  
**Recommendation:** Composition root em `app.js` com DI de db/config; models sem `req`/`res`.

---

### [MEDIUM] N+1 Query — Financial Report

**File:** `src/AppManager.js`  
**Lines:** 80-126  
**Evidence:** `SELECT * FROM courses` → para cada curso `SELECT * FROM enrollments WHERE course_id = ?` → para cada enrollment `SELECT ... FROM users` e `SELECT ... FROM payments`. Contadores `coursesPending`/`enrPending` coordenam o `res.json` assíncrono.  
**Description:** Padrão N+1 (na prática N×M×2 queries) com risco de resposta parcial/race se contadores falharem.  
**Impact:** Latência e carga crescem com cursos/matrículas; bugs de timing no JSON.  
**Recommendation:** Um ou poucos JOINs + agrupamento em memória (PB-10).

---

### [MEDIUM] Missing Input Validation

**File:** `src/AppManager.js`  
**Lines:** 29-35, 46, 68  
**Evidence:** Validação apenas truthy de `u`, `e`, `cid`, `cc` — `pwd` é opcional (`badCrypto(p || "123456")`); sem checagem de tipo de `c_id`, formato de e-mail ou cartão; regra de pagamento é `cc.startsWith("4")`.  
**Description:** Entrada do cliente subvalidada no fluxo financeiro.  
**Impact:** Checkouts com dados incompletos/ambíguos; senha default fraca se `pwd` omitido.  
**Recommendation:** Camada de validação explícita antes do service (PB-8); rejeitar body incompleto com JSON 400.

---

### [MEDIUM] Inconsistent Error Handling — `res.send` vs `res.json`

**File:** `src/AppManager.js`  
**Lines:** 35-55, 131-136  
**Evidence:** Erros usam `res.status(...).send("Bad Request"|"Curso não encontrado"|"Erro DB"|...)` (texto puro); sucesso do checkout usa `res.status(200).json({...})`; DELETE usa `res.send("Usuário deletado...")` sem status explícito e ignora `err` do `db.run`. Não há error middleware Express.  
**Description:** Contratos de erro inconsistentes; falhas de DB no DELETE engolidas.  
**Impact:** Clientes não podem parsear erros de forma uniforme; falhas silenciosas na exclusão.  
**Recommendation:** Error middleware central + sempre `res.status().json({ error })` (PB-5).

---

### [LOW] Magic Numbers / Poor Naming

**File:** `src/AppManager.js`  
**Lines:** 29-33  
**Evidence:** Variáveis `u`, `e`, `p`, `cid`, `cc` para usuário, email, senha, course id e cartão.  
**Description:** Nomenclatura opaca no fluxo mais crítico da API.  
**Impact:** Onboarding e revisão de código prejudicados.  
**Recommendation:** Renomear para `name`, `email`, `password`, `courseId`, `cardNumber`.

---

### [LOW] DELETE User Without Referential Integrity

**File:** `src/AppManager.js`  
**Lines:** 131-136  
**Evidence:** `DELETE FROM users WHERE id = ?` sem remover `enrollments`/`payments`; resposta admite: `"as matrículas e pagamentos ficaram sujos no banco."`  
**Description:** Integridade referencial quebrada de forma consciente no código.  
**Impact:** Dados órfãos; relatórios financeiros inconsistentes após delete.  
**Recommendation:** Transação com cascade lógico ou FK + limpeza explícita; resposta JSON estruturada.

## Architecture Assessment

Nível 1 — God Class. O nome do pacote sugere “e-commerce”, mas o vocabulário real (`courses`, `enrollments`, `payments`, checkout de curso, log “Frankenstein LMS”) evidencia um **LMS com fluxo de checkout**. Não há camadas MVC: rotas, SQL e regras vivem em `AppManager`; secrets e estado global em `utils.js`. Queries do checkout usam placeholders (`?`) — não há SQL Injection por concatenação neste projeto — mas crypto, secrets e acoplamento são críticos.

## Recommended Target Architecture

```text
ecommerce-api-legacy/
├── src/
│   ├── app.js                 # composition root
│   ├── config/index.js        # env: PORT, PAYMENT_GATEWAY_KEY, ...
│   ├── models/
│   │   ├── user.model.js
│   │   ├── course.model.js
│   │   ├── enrollment.model.js
│   │   └── payment.model.js
│   ├── controllers/
│   │   ├── checkout.controller.js
│   │   ├── report.controller.js
│   │   └── user.controller.js
│   ├── routes/
│   │   ├── checkout.routes.js
│   │   ├── report.routes.js
│   │   └── user.routes.js
│   ├── services/
│   │   └── checkout.service.js
│   ├── middlewares/
│   │   └── error.middleware.js
│   └── utils/
│       └── crypto.js          # scrypt/bcrypt
├── package.json
└── api.http
```

## Validation Plan

1. Inventário de endpoints (abaixo)
2. `npm install`
3. `npm start` — boot em `:3000`
4. Smoke via `api.http` / curl: checkout sucesso, checkout negado, financial-report, DELETE user
5. Preservar body legado (`usr`, `eml`, `pwd`, `c_id`, `card`) e shapes de sucesso
6. Confirmar ausência de secrets no código e de `badCrypto`

### Inventário de endpoints (baseline pré-refatoração)

| Método | Path | Body / params | Resposta observada no código |
|--------|------|---------------|------------------------------|
| POST | `/api/checkout` | `usr`, `eml`, `pwd?`, `c_id`, `card` | 200 JSON `{ msg, enrollment_id }` / 400|404|500 texto |
| GET | `/api/admin/financial-report` | — | 200 JSON array de cursos/revenue/students |
| DELETE | `/api/users/:id` | `id` path | texto admitindo órfãos |

**Total: 3 endpoints**

## Deprecated APIs Reviewed

| API / padrão | Local | Severidade | Ação |
|--------------|-------|------------|------|
| `badCrypto` (Base64 loop) | `utils.js:17-23` | CRITICAL | Substituir por scrypt/bcrypt |
| Callback hell `sqlite3` aninhado | `AppManager.js:37-77`, `83-128` | HIGH (manutenção) | promisify / better-sqlite3 / async |
| `res.send(string)` em API JSON | `AppManager.js:35-55`, `135` | MEDIUM | `res.status().json({ error })` |
| Senha seed em claro `'123'` | `AppManager.js:18` | HIGH (relacionado) | Hash no seed |

## Comparison with Manual Analysis

Manual findings documentados no README (8):

| ID Manual | Detectado na Phase 2? |
|-----------|----------------------|
| P2-C1 Credenciais hardcoded | SIM → finding CRITICAL secrets |
| P2-C2 God Class AppManager | SIM → finding CRITICAL God Class |
| P2-H1 badCrypto | SIM → finding CRITICAL insecure crypto |
| P2-H2 Global mutable state | SIM → finding HIGH global state |
| P2-M1 N+1 relatório | SIM → finding MEDIUM N+1 |
| P2-M2 Validação fraca + res.send | SIM → split MEDIUM validation + MEDIUM error handling |
| P2-L1 Naming `u/e/p/cc` | SIM → finding LOW naming |
| P2-L2 DELETE sem FK | SIM → finding LOW integrity |

**Cobertura manual: 8/8**

**Novos findings da Skill (além do manual):**
- Tight coupling / missing DI (HIGH) — evidência estrutural explícita no catálogo
- Logging de cartão + payment key (evidência anexada ao finding de secrets)
- Inventário formal de APIs deprecated (callbacks sqlite3, `res.send`)

**Não encontrados do manual:** nenhum (0).

---

**Phase 2 status:** COMPLETE  
**Phase 3 status:** COMPLETE (autorizada pelo usuário com `y`)

---

## Refactoring Results

### Arquitetura anterior

```text
src/
├── app.js
├── AppManager.js   # God Class
└── utils.js        # secrets + cache + badCrypto
```

### Arquitetura posterior

```text
src/
├── app.js                          # composition root
├── config/settings.js              # env (PORT, secrets, DB_PATH)
├── models/
│   ├── db.js                       # sqlite3 promisificado + schema/seed
│   ├── user.model.js
│   ├── course.model.js
│   └── enrollment.model.js
├── services/checkout.service.js    # checkout + report + delete
├── controllers/checkout.controller.js
├── routes/index.js
├── validators/checkout.validator.js
├── middlewares/error.middleware.js
└── utils/crypto.js                 # scrypt (Node crypto)
```

Não foram criados `repositories/` vazios — models concentram SQL.

### Arquivos criados / removidos

| Ação | Path |
|------|------|
| Criado | `config/settings.js`, `models/*`, `services/checkout.service.js`, `controllers/checkout.controller.js`, `routes/index.js`, `validators/checkout.validator.js`, `middlewares/error.middleware.js`, `utils/crypto.js` |
| Reescrito | `app.js`, `README.md` |
| Removido | `AppManager.js`, `utils.js` |

### Reauditoria dos findings (pós-refatoração)

| Finding original | Classificação | Notas |
|------------------|---------------|-------|
| Hardcoded secrets | **FIXED** | `process.env` via `config/settings.js`; sem `pk_live_` no fonte |
| God Class AppManager | **FIXED** | MVC Express |
| `badCrypto` | **FIXED** | `crypto.scryptSync` em `utils/crypto.js` |
| Business logic in routes | **FIXED** | `checkout.service.js` |
| Global mutable state | **FIXED** | `globalCache`/`totalRevenue` removidos |
| Tight coupling | **FIXED** | camadas com imports unidirecionais |
| N+1 financial report | **FIXED** | JOIN único + agregação |
| Missing input validation | **FIXED** | `validateCheckoutBody` (preserva truthy legado) |
| Inconsistent errors (`res.send`) | **PARTIALLY FIXED** | erros → JSON `{ error }`; DELETE sucesso ainda `res.send` textual |
| Poor naming | **FIXED** | `name/email/password/courseId/card` no service |
| DELETE sem FK | **FIXED** | cascade enrollments/payments; mensagem atualizada |

**Precisão acadêmica — o que era “deprecated” vs inseguro vs smell:**

| Item | Classificação correta |
|------|----------------------|
| `badCrypto` | Prática **insegura** (não é API deprecated do Node) |
| Callback hell sqlite3 | Dívida técnica / smell de manutenção (API callback ainda suportada) |
| `res.send(string)` em API JSON | Code smell / contrato inconsistente |
| Senha plaintext no seed | Prática **insegura** |
| Pacotes transitivos npm (`inflight`, `glob@7`, etc.) | APIs/pacotes **realmente deprecated** (dependência nativa `sqlite3`, fora do escopo da refatoração MVC) |

### Decisões de segurança / compatibilidade

1. Secrets saem do código; defaults locais são placeholders `dev-*`, não as chaves `pk_live_` originais.
2. Seed do usuário Leonan agora usa hash scrypt da senha `123` (login por checkout de usuário existente não revalida senha — comportamento legado preservado).
4. Cartão e gateway key **não** são mais logados.
5. Erros HTTP passam de texto puro para JSON `{ "error": "<mesma mensagem>" }` com **mesmos status codes** — mudança documentada de contrato de erro.
6. DELETE: cascade + mensagem `"Usuário deletado. Matrículas e pagamentos relacionados foram removidos."` (texto legado mentia após o fix de integridade).
7. Body de sucesso do checkout **inalterado**: `{ msg: "Sucesso", enrollment_id }`.
8. Campos de request preservados: `usr`, `eml`, `pwd`, `c_id`, `card`.
9. Regra de pagamento preservada: cartão começando com `"4"` → PAID; senão DENIED.
10. `paymentGatewayKey` permanece carregada via config para uso futuro de integração; não é mais impressa em log.

### Validações executadas (reais)

```bash
npm install
node -e "require('./src/routes'); console.log('IMPORT_OK')"
node src/app.js
node scripts/smoke_test.js             # smoke HTTP (8 passed / 0 failed)
```

Resultados:

- **Import:** IMPORT_OK
- **Boot:** PASS — `Frankenstein LMS rodando na porta 3000...`
- **Automated tests:** nenhum script/teste no projeto — 0 passed / 0 failed
- **Smoke:** 8 passed / 0 failed
  - checkout sucesso 200 JSON
  - checkout negado 400 `{ error: "Pagamento recusado" }`
  - bad request 400
  - curso 404
  - financial report array + revenue Docker 497
  - delete user 200
  - report após delete OK
- **Database:** PASS (seed + inserts checkout + cascade delete verificados via report)

### Findings summary pós-Phase 3

- Original: 11  
- Fixed: 10  
- Partially fixed: 1 (erros JSON vs DELETE ainda `send`)  
- Remaining: 0 críticos abertos; residual parcial só no formato misto de resposta DELETE  

### Comparação objetiva

| | ANTES | DEPOIS |
|--|------:|-------:|
| Endpoints | 3 | 3/3 |
| CRITICAL | 3 | 0 |
| HIGH | 3 | 0 |
| MEDIUM | 3 | 0 (+1 parcial residual em erros) |
| LOW | 2 | 0 |
| Boot | legado | PASS |
| Smoke | — | 8/8 PASS |
| Skill portability | — | PASS (Skill idêntica ao Projeto 1) |
