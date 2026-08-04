# Refactoring Playbook

Padrões de transformação concretos. Adapte à stack detectada na Fase 1.
Cada padrão: problema → sinais → objetivo → BEFORE/AFTER → passos → validação → riscos.

---

## PB-1 — God Class / God Module → divisão MVC

**Problema:** Um arquivo/classe concentra vários domínios + HTTP + SQL.

**Sinais:** Múltiplos verbos de domínio no mesmo módulo; >200 linhas; rotas dentro da classe.

**Objetivo:** Separar por responsabilidade e domínio.

### BEFORE (Python)

```python
# models.py — produtos + usuarios + pedidos + relatorios
def get_produto_por_id(id): ...
def login_usuario(email, senha): ...
def relatorio_vendas(): ...
```

### AFTER (Python)

```text
models/produto_model.py
models/usuario_model.py
models/pedido_model.py
controllers/produto_controller.py
views/routes.py
```

### BEFORE (JavaScript)

```javascript
class LegacyApplication {
  setupRoutes(app) { app.post('/api/orders', ...); app.get('/api/admin/report', ...); }
}
```

### AFTER (JavaScript)

```text
routes/order.routes.js
controllers/order.controller.js
models/order.model.js
config/index.js
```

**Passos:** 1) Mapear funções por domínio 2) Criar módulos 3) Atualizar imports 4) Entry point só compõe.

**Validação:** Endpoints idênticos; boot OK.

**Riscos:** Quebrar imports circulares — preferir imports unidirecionais (routes→controllers→models).

---

## PB-2 — Route com business logic → Controller/Service

**Problema:** Handler HTTP calcula, persiste e notifica.

**Sinais:** 40+ linhas na rota; callback aninhado; prints de “ENVIANDO EMAIL” na rota.

**Objetivo:** Route fina; controller/service com a regra.

### BEFORE (Express)

```javascript
app.post('/api/orders', (req, res) => {
  // valida, busca item, cria user, processa pagamento, persiste, audita...
});
```

### AFTER (Express)

```javascript
// routes/order.routes.js
router.post('/api/orders', orderController.create);

// controllers/order.controller.js
async function create(req, res, next) {
  try {
    const result = await orderService.process(req.body);
    res.status(200).json(result);
  } catch (e) { next(e); }
}
```

**Passos:** Extrair função de domínio → injetar deps → rota só delega.

**Validação:** Mesmo body/response do inventário.

**Riscos:** Mudar formato de erro — preservar status e shape quando possível.

---

## PB-3 — SQL em route/model inseguro → Model/Repository parametrizado

**Problema:** Concatenação SQL / SQL na rota.

**Sinais:** `"WHERE id = " + str(id)`; endpoint `sql` livre.

**Objetivo:** Prepared statements; SQL só no model; remover SQL arbitrário ou proteger fortemente.

### BEFORE (Python)

```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```

### AFTER (Python)

```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```

### BEFORE (Node)

```javascript
db.run("DELETE FROM users WHERE id = " + id);
```

### AFTER (Node)

```javascript
db.run("DELETE FROM users WHERE id = ?", [id]);
```

**Passos:** Substituir concat por placeholders; mover SQL da rota para model; **se o endpoint de SQL livre for preservado por contrato, torná-lo obrigatoriamente: (1) autenticado (papel admin), (2) allowlist de comandos/tabelas (ex.: só SELECT), (3) rejeitar multi-statement/DML/DDL — caso contrário, eliminar a rota.**

**Validação:** CRUD funciona; tentativa de injeção falha com segurança; `/admin/query` sem auth retorna 401; não-admin 403; `DROP`/`DELETE` rejeitados.

**Riscos:** Mudar tipo de parâmetro (string vs int).

---

## PB-4 — Secret hardcoded → environment/config

**Problema:** Secrets no código.

**Sinais:** `SECRET_KEY = "..."`, `pk_live_`, senha SMTP no fonte.

**Objetivo:** Config central lendo env.

### BEFORE (Python)

```python
app.config["SECRET_KEY"] = "***REDACTED***"
```

### AFTER (Python)

```python
# config/settings.py
import os
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

### BEFORE (JavaScript)

```javascript
const config = { paymentGatewayKey: "pk_live_***REDACTED***" };
```

### AFTER (JavaScript)

```javascript
module.exports = {
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
  port: Number(process.env.PORT || 3000),
};
```

**Passos:** Criar config → trocar literais → remover secrets de health responses → documentar `.env.example`.

**Validação:** App sobe com env; health não vaza secret.

**Riscos:** Esquecer de setar env em produção.

---

## PB-5 — Error handling duplicado → middleware centralizado

**Problema:** try/except idêntico em cada handler; respostas inconsistentes.

**Sinais:** `except Exception as e: return jsonify({"erro": str(e)}), 500` repetido; `res.send("Erro DB")`.

**Objetivo:** Um error handler; controllers levantam erros de domínio.

### AFTER (Flask)

```python
@app.errorhandler(AppError)
def handle_app_error(e):
    return jsonify({"erro": e.message, "sucesso": False}), e.status
```

### AFTER (Express)

```javascript
function errorHandler(err, req, res, next) {
  const status = err.status || 500;
  res.status(status).json({ error: err.message || 'Internal Error' });
}
app.use(errorHandler);
```

**Validação:** 404/400/500 ainda retornam JSON coerente.

**Riscos:** Expor stack traces — não vazar em produção.

---

## PB-6 — Código duplicado → função/service compartilhado

**Problema:** Mesma lógica copiada.

**Sinais:** Validação POST≈PUT; `is_overdue` em 5 lugares.

**Objetivo:** Uma implementação canônica.

### BEFORE

```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != 'done' and t.status != 'cancelled':
            overdue = True
```

### AFTER

```python
# no model
def is_overdue(self):
    ...
# na rota
data['overdue'] = task.is_overdue()
```

**Validação:** Comportamento de overdue idêntico.

**Riscos:** Divergência sutil de timezone ao unificar.

---

## PB-7 — Global mutable state → dependência encapsulada

**Problema:** `global db_connection`, `globalCache = {}`.

**Objetivo:** Ciclo de vida explícito (app context, DI, pool).

### BEFORE (Python)

```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect(...)
```

### AFTER (Python)

```python
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db
```

**Validação:** Requests concorrentes não corrompem estado; testes isoláveis.

**Riscos:** `check_same_thread` / conexões por request vs singleton.

---

## PB-8 — Input sem validação → validation layer

**Problema:** Body usado sem schema.

**Objetivo:** Validar antes do domínio.

### AFTER (Python)

```python
def validate_produto_payload(dados):
    if not dados or "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    ...
    return ProdutoDTO(...)
```

### AFTER (JavaScript)

```javascript
function validateCheckout(body) {
  const errors = [];
  if (!body.eml) errors.push('eml required');
  if (!body.c_id) errors.push('c_id required');
  if (!body.card) errors.push('card required');
  return errors;
}
```

**Validação:** Payloads inválidos → 400 com mensagem clara.

**Riscos:** Over-validation que quebra clientes existentes — preservar contratos.

---

## PB-9 — Deprecated API → API suportada

**Problema:** APIs obsoletas/inseguras.

### Exemplos

| Antes | Depois |
|-------|--------|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| `hashlib.md5(pwd)` | `bcrypt.hashpw` / werkzeug `generate_password_hash` |
| `badCrypto(pwd)` | `crypto.scryptSync` / bcrypt |
| `debug=True` hardcoded | `DEBUG` via env |
| `res.send("Bad Request")` | `res.status(400).json({ error: 'Bad Request' })` |
| `User.query.get(id)` | `db.session.get(User, id)` |

**Validação:** Testes de login/hash; app sobe sem warnings críticos.

**Riscos:** Hashes antigos incompatíveis — migrar com rehash no login ou flag de versão.

---

## PB-10 — Query N+1 → estratégia otimizada

**Problema:** Loop + query por item.

### BEFORE (Python)

```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
```

### AFTER (Python)

```python
cursor.execute("""
  SELECT p.*, i.produto_id, i.quantidade, pr.nome AS produto_nome
  FROM pedidos p
  LEFT JOIN itens_pedido i ON i.pedido_id = p.id
  LEFT JOIN produtos pr ON pr.id = i.produto_id
  WHERE p.usuario_id = ?
""", (usuario_id,))
# agrupar em memória por pedido_id
```

### BEFORE (Node N+1)

```javascript
courses.forEach(c => {
  db.all("SELECT * FROM enrollments WHERE course_id = ?", [c.id], ...);
});
```

### AFTER

```javascript
// Uma query com JOINs users/enrollments/payments/courses, depois groupBy course_id
```

**Validação:** Mesmo JSON; menos queries (logar ou contar).

**Riscos:** JOIN explode linhas — agrupar corretamente.

---

## Ordem sugerida na Fase 3

1. Inventário de endpoints  
2. Config + secrets (PB-4)  
3. Estrutura MVC (PB-1)  
4. SQL seguro (PB-3) + N+1 (PB-10)  
5. Extrair lógica das rotas (PB-2)  
6. Validação e erros (PB-8, PB-5)  
7. Estado global e deprecated (PB-7, PB-9)  
8. DRY (PB-6)  
9. Boot + smoke tests  
