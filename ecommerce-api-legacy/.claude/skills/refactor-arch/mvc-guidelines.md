# MVC Guidelines para APIs REST

MVC em APIs **não** significa templates HTML. Adapte as responsabilidades:

| MVC clássico | API REST |
|--------------|----------|
| View | Camada HTTP (routes) + serialização |
| Controller | Coordenação do caso de uso |
| Model | Domínio + persistência |

---

## Model

**Responsável por:**
- Entidades e regras diretamente associadas ao domínio
- Acesso/persistência (queries, ORM, repositórios)
- Invariantes do modelo (estoque >= 0, status válidos no domínio)

**Não deve:**
- Importar `request`, `response`, `jsonify`, `res`, `req`
- Conhecer status HTTP
- Conter configuração de servidor ou secrets de aplicação (exceto se for value object de domínio)

**Exemplos por stack:**
- Python: `ProdutoModel.create(...)`, classes SQLAlchemy
- Node: `userRepository.findByEmail(email)`, models Sequelize/Prisma

---

## View / Routes

**Responsável por:**
- Declarar endpoints (path + método)
- Extrair entrada (`params`, `query`, `body`, headers)
- Delegar ao controller
- Retornar response (JSON + status)

**Não deve:**
- Conter lógica complexa de negócio
- Abrir conexões SQL diretamente (exceto health check trivial, preferencialmente via model)
- Implementar regras financeiras, hashing, N+1 manual

**Exemplos:**
- Flask Blueprint / `add_url_rule` apontando para controller
- Express `Router` chamando `controller.checkout(req, res, next)`

---

## Controller

**Responsável por:**
- Coordenar o fluxo do caso de uso
- Chamar models e/ou services
- Traduzir resultados de domínio em DTOs/dict
- Decidir status HTTP com base no resultado (not found, conflict, etc.)
- Acionar side-effects via services (email, auditoria)

**Não deve:**
- Ser um “God Controller” com SQL cru de vários domínios
- Duplicar validações massivas — preferir validators/schemas

---

## Config

**Centralizar:**
- Variáveis de ambiente
- Connection strings
- Secrets (`SECRET_KEY`, API keys, SMTP)
- Flags (`DEBUG`, `PORT`)

**Regras:**
- Nunca hardcodar secrets no código
- Fornecer defaults seguros só para desenvolvimento local (e documentar)
- Entry point lê config; demais camadas recebem valores já resolvidos

---

## Middleware

**Responsabilidades transversais:**
- Autenticação / autorização
- Logging estruturado
- Tratamento de erros (converter exceções em JSON)
- CORS, rate limit, request ID
- Validações globais (content-type)

**Flask:** `@app.errorhandler`, `before_request`
**Express:** `app.use((err, req, res, next) => ...)`

---

## Services (opcional)

Use quando:
- A regra é reutilizada por múltiplos controllers
- Há integração externa (pagamento, email, SMS)
- O fluxo ultrapassa um único model

Não crie service “por arquivo” sem necessidade — YAGNI.

---

## Entry point / Composition root

- Cria app (`Flask(__name__)` / `express()`)
- Carrega config
- Registra middlewares, rotas e error handlers
- Não contém regra de negócio

---

## Mapa por nível de organização atual

| Nível atual | Estratégia Fase 3 |
|-------------|-------------------|
| Monólito plano (4 arquivos) | Criar `config/`, `models/`, `controllers/`, `views/`, `middlewares/` |
| God Class Express | Extrair `routes/`, `controllers/`, `models/`, `config/`, `middlewares/` |
| Camadas parciais | Manter pastas; extrair controllers; corrigir vazamentos; config; middleware de erro |
| Quase MVC | Correções pontuais (secrets, hash, N+1, deprecated) |

**Não destrua uma organização boa só para recriar diretórios.**
