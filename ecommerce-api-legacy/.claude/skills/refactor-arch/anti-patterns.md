# Catálogo de Anti-Patterns

Use este catálogo na Fase 2. Para cada item: procurar sinais → se ausente, **não reportar**.
Severidade padrão pode ser elevada/reduzida conforme impacto real no projeto.

---

## 1. God Class / God Module

**Definição:** Uma classe ou módulo concentra múltiplos domínios, persistência, HTTP e regras de negócio.

**Sinais:**
- Arquivo > ~200 linhas com 3+ domínios distintos (users + products + orders + reports)
- Uma classe registra rotas, abre DB, processa pagamento e gera relatório
- Funções sem coesão no mesmo módulo (`get_produto`, `login_usuario`, `relatorio_vendas`)

**Falsos positivos:** Facade fina que só delega; arquivo de rotas que só mapeia handlers.

**Severidade padrão:** CRITICAL (se concentra segurança+persistência+HTTP) ou HIGH.

**Elevar:** Contém credenciais + SQL + rotas no mesmo arquivo.
**Reduzir:** Módulo grande mas com um único domínio coeso.

**Correção:** Dividir por domínio em Models + Controllers + Routes (ver playbook PB-1).

---

## 2. Hardcoded Credentials / Secrets

**Definição:** Segredos, chaves de API, senhas de DB/SMTP ou SECRET_KEY embutidos no código-fonte.

**Sinais:**
- `SECRET_KEY = "..."`, `password = "..."`, prefixos de chave `pk_live_` / `sk_live_` (padrões, não valores reais)
- `dbPass`, `smtpPassword`, `email_password = '...'`
- Health endpoints que retornam a secret key no JSON

**Falsos positivos:** Placeholders óbvios em `.env.example` (`CHANGE_ME`); hashes de seed de demo claramente documentados (avaliar contexto).

**Severidade padrão:** CRITICAL.

**Elevar:** Credenciais de produção reais + endpoint público que as expõe.
**Reduzir:** Apenas DEBUG flag sem secret (virar HIGH/MEDIUM).

**Correção:** `os.environ` / `process.env` + módulo Config; nunca serializar secrets (PB-4).

---

## 3. SQL Injection / Unsafe Query Construction

**Definição:** Queries montadas por concatenação/interpolação com dados externos.

**Sinais:**
- Python: `cursor.execute("... " + var)`, `f"SELECT ... {var}"`, `"WHERE id = " + str(id)`
- Node: `` db.query(`...${id}`) ``, `"SELECT ... " + req.body`
- Endpoint que executa SQL arbitrário enviado pelo cliente (`dados.get("sql")`)

**Falsos positivos:** SQL estático sem variáveis; `execute(sql, (param,))` / `?` placeholders.

**Severidade padrão:** CRITICAL.

**Elevar:** Endpoint admin aberto executando SQL livre.
**Reduzir:** Concatenação só com IDs internos tipados int (ainda HIGH, mas documentar).

**Correção:** Prepared statements / ORM parametrizado (PB-3).

---

## 4. Business Logic in Routes / Controllers

**Definição:** Regras de negócio complexas, orquestração de persistência e side-effects dentro da camada HTTP.

**Sinais:**
- Handler de rota com 40+ linhas misturando validação, cálculo, SQL e notificação
- Callback hell em rota Express (3+ níveis aninhados de DB)
- Duplicação da mesma regra de domínio em várias rotas

**Falsos positivos:** Controller fino que chama service e formata resposta; validação de schema HTTP simples.

**Severidade padrão:** HIGH.

**Elevar:** Lógica financeira/pagamento na rota.
**Reduzir:** Poucas linhas de validação de presença de campos (MEDIUM/LOW).

**Correção:** Extrair Controller/Service; routes só HTTP (PB-2).

---

## 5. Tight Coupling / Missing Dependency Boundaries

**Definição:** Módulos dependem de singletons globais, caminhos concretos ou detalhes de infraestrutura misturados ao domínio.

**Sinais:**
- Import direto de conexão global em toda função
- Model que importa Flask `request`/`jsonify`
- Classe que instancia DB, gateway de pagamento e SMTP internamente sem injeção

**Falsos positivos:** Composition root (entry point) que monta dependências.

**Severidade padrão:** HIGH.

**Correção:** Injeção de dependência; models sem HTTP; config centralizada.

---

## 6. Global Mutable State

**Definição:** Estado compartilhado mutável em escopo de módulo (cache, conexões, contadores) acessível globalmente.

**Sinais:**
- Python: `db_connection = None` + `global db_connection`
- JS: `let globalCache = {}`, `let totalRevenue = 0` no módulo
- Listas de notificações em memória em instâncias singleton implícitas

**Falsos positivos:** Constantes imutáveis (`VALID_STATUSES = [...]`).

**Severidade padrão:** HIGH.

**Correção:** Encapsular em classe/serviço com ciclo de vida claro; connection-per-request ou pool (PB-7).

---

## 7. Duplicated Code

**Definição:** Blocos idênticos ou quase idênticos repetidos (DRY violado).

**Sinais:**
- Mesma validação de produto em POST e PUT
- Mesma lógica `is_overdue` copiada em 3+ handlers
- Serialização manual de entidade repetida em vez de `to_dict`

**Falsos positivos:** APIs distintas com coincidência superficial.

**Severidade padrão:** MEDIUM.

**Correção:** Extrair função/validator/helper compartilhado (PB-6).

---

## 8. Missing Input Validation

**Definição:** Entrada do cliente usada sem checagem de tipo, presença, faixa ou formato.

**Sinais:**
- `request.get_json()` usado direto em SQL/ORM sem checagens
- Checkout que só verifica “campo truthy”
- Conversões sem try (`int(priority)` pode explodir)
- Ausência de validação de status/role/enum

**Falsos positivos:** Validação presente mas verbosa (ainda pode haver duplicação).

**Severidade padrão:** MEDIUM (HIGH se leva a SQLi ou corrupção financeira).

**Correção:** Camada de validação / schema (marshmallow, zod, joi, funções dedicadas) (PB-8).

---

## 9. N+1 Query

**Definição:** Loop sobre N registros dispara query adicional por item (e às vezes por subitem).

**Sinais:**
- `for row in pedidos: cursor.execute(... WHERE pedido_id = ...)`
- `courses.forEach` → `enrollments` → `users` → `payments` (Node callbacks)
- `for t in tasks: User.query.get(t.user_id)` sem eager load

**Falsos positivos:** Uma query única com JOIN; `joinedload` / `include`.

**Severidade padrão:** MEDIUM.

**Correção:** JOIN, batch fetch, eager loading (PB-10).

---

## 10. Magic Numbers / Poor Naming

**Definição:** Literais sem nome semântico; identificadores opacos (`u`, `e`, `p`, `cc`).

**Sinais:**
- `if faturamento > 10000: desconto = faturamento * 0.1`
- Variáveis de 1 letra para entidades de negócio
- Portas/timeouts literais espalhados

**Falsos positivos:** `0`, `1`, HTTP status codes bem conhecidos (`404`).

**Severidade padrão:** LOW.

**Correção:** Constantes nomeadas; nomes descritivos.

---

## 11. Inconsistent Error Handling

**Definição:** Mistura de padrões de erro (try/except duplicado, bare except, `res.send` string vs JSON, status inconsistentes).

**Sinais:**
- `except:` sem tipo / `except Exception` que engole tudo em cada rota
- Mesmo erro às vezes 400, às vezes 500
- Express: `res.send("Bad Request")` misturado com `res.json(...)`
- Sem error middleware central

**Falsos positivos:** Handler central único + re-raise controlado.

**Severidade padrão:** MEDIUM.

**Correção:** Middleware/error handler centralizado (PB-5).

---

## 12. Deprecated APIs

**Definição:** Uso de APIs/bibliotecas marcadas como deprecated ou inseguras por padrão moderno.

**Sinais obrigatórios a verificar:**

| Sinal | Stack | Substituir por |
|-------|-------|----------------|
| `datetime.utcnow()` | Python 3.12+ | `datetime.now(timezone.utc)` |
| `datetime.utcfromtimestamp` | Python 3.12+ | `datetime.fromtimestamp(..., tz=timezone.utc)` |
| `hashlib.md5` para senhas | Qualquer | bcrypt/argon2/scrypt (+ salt) |
| Crypto caseiro (`badCrypto`, base64 loop) | Node | `crypto.scrypt` / bcrypt |
| `app.run(debug=True)` em código “produção” | Flask | debug via env; nunca default True em prod |
| `Flask(debug=True)` / `DEBUG = True` hardcoded | Flask | `os.getenv("FLASK_DEBUG")` |
| `User.query.get()` (SQLAlchemy 2.x style legacy) | Flask-SQLAlchemy | `db.session.get(User, id)` |
| `res.send(string)` para API JSON | Express | `res.status(...).json(...)` |
| Callback-only `sqlite3` aninhado profundo | Node | `util.promisify` / better-sqlite3 / sqlite async |

**Falsos positivos:** MD5 para checksum não-senha; `debug=True` apenas em README de demo (ainda reportar no código).

**Severidade padrão:**
- Crypto/hash inseguro para senhas → CRITICAL
- `utcnow` → LOW/MEDIUM
- `debug=True` hardcoded → HIGH (com secret) ou MEDIUM
- Callback hell estilo deprecated pattern → HIGH (como smell de manutenção)

**Correção:** Ver PB-9.

---

## Guia rápido de severidade

| Severidade | Quando usar |
|------------|-------------|
| CRITICAL | Compromete segurança ou integridade (SQLi, secrets, hash fraco de senha, SQL admin aberto, God Class destrutiva) |
| HIGH | Viola MVC/SOLID de forma grave (lógica na rota, acoplamento, estado global, auth fake) |
| MEDIUM | Duplicação, N+1, validação fraca, erros inconsistentes |
| LOW | Naming, magic numbers, APIs deprecated de baixo risco, dead code menor |
