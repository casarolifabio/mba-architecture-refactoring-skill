# MBA — Skill de Auditoria e Refatoração Arquitetural (`refactor-arch`)

Skill para **Claude Code** que audita e refatora projetos legados para o padrão **MVC** em três fases (Análise → Auditoria com confirmação humana → Refatoração + Validação). Agnóstica de tecnologia; validada conceitualmente sobre Python/Flask e Node.js/Express.

- **Ferramenta:** Claude Code (`.claude/skills/refactor-arch/`)
- **Invocação:** `claude "/refactor-arch"` dentro de cada projeto
- **Repositório base:** [devfullcycle/mba-ia-refactor-projects-skill](https://github.com/devfullcycle/mba-ia-refactor-projects-skill)

---

## Análise Manual

> As referências de arquivo e linha desta seção correspondem ao código legado original, antes da execução da Phase 3. Alguns desses arquivos foram posteriormente movidos, divididos ou removidos durante a refatoração MVC.

Auditoria humana realizada sobre o código **legado original** dos três projetos, antes da criação da Skill. Todos os findings abaixo possuem arquivo e linhas verificados no fonte legado.

### Projeto 1 — `code-smells-project`

| ID | Severidade | Problema | Arquivo/Linhas | Impacto |
| -- | ---------- | -------- | -------------- | ------- |
| P1-C1 | CRITICAL | SQL Injection por concatenação de strings | `models.py:28-297` | Execução arbitrária de SQL; comprometimento do banco |
| P1-C2 | CRITICAL | Endpoint `/admin/query` executa SQL livre do cliente | `app.py:59-78` | RCE lógico no banco sem autenticação |
| P1-C3 | CRITICAL | `SECRET_KEY` hardcoded e `DEBUG=True` | `app.py:7-8` | Sessões previsíveis; vazamento de debug em exposição pública |
| P1-H1 | HIGH | God Module — quatro domínios em um único `models.py` | `models.py:1-315` | Impossível testar/isolar; qualquer mudança afeta tudo |
| P1-H2 | HIGH | Health check expõe `secret_key` e metadados sensíveis | `controllers.py:276-289` | Vazamento ativo de segredo via endpoint público |
| P1-M1 | MEDIUM | N+1 em listagem de pedidos (itens + nome do produto) | `models.py:171-233` | Degradação de performance proporcional ao volume |
| P1-M2 | MEDIUM | Validação de produto duplicada em criar/atualizar | `controllers.py:28-54` e `72-90` | Drift de regras; manutenção duplicada |
| P1-L1 | LOW | Magic numbers nas faixas de desconto do relatório | `models.py:256-262` | Regra de negócio opaca |
| P1-L2 | LOW | Uso de `print()` como logging | `controllers.py:8-220` | Observabilidade inadequada |

#### Detalhamento — Projeto 1

**P1-C1 — SQL Injection.** Em `get_produto_por_id`, `criar_produto`, `login_usuario`, `buscar_produtos` e demais funções, o SQL é montado com `+` e valores vindos da aplicação/cliente (`models.py:28`, `47-50`, `109-111`, `289-297`). Um payload em nome/email/termo de busca altera a query.

**P1-C2 — SQL administrativo aberto.** `POST /admin/query` lê `dados["sql"]` e chama `cursor.execute(query)` sem autenticação nem allowlist (`app.py:59-78`).

**P1-C3 — Secrets e debug.** `SECRET_KEY` e `DEBUG` fixos no entry point (`app.py:7-8`); o servidor sobe com `debug=True` (`app.py:88`).

**P1-H1 — God Module.** Um único módulo implementa produtos, usuários, pedidos, itens e relatório de vendas (`models.py:1-315`), misturando persistência e regras.

**P1-H2 — Vazamento no health.** O JSON de `/health` inclui o campo `secret_key` com a chave da aplicação (`controllers.py:289`).

> O valor original presente no código legado foi redigido neste relatório por segurança. O finding foi identificado antes da refatoração.

**P1-M1 — N+1.** Para cada pedido, nova query de itens; para cada item, nova query de produto (`models.py:187-199`, `219-231`).

**P1-M2 — Duplicação.** As mesmas checagens de nome/preço/estoque aparecem em `criar_produto` e `atualizar_produto`.

**P1-L1 / P1-L2.** Limiares `10000/5000/1000` e taxas `0.1/0.05/0.02` sem constantes; logs via `print`.

**Evidências de stack (confirmadas):** Python 3 + Flask 3.1.1 + flask-cors; SQLite via `sqlite3`; domínio e-commerce (produtos, usuários, pedidos); monólito plano em 4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`).

---

### Projeto 2 — `ecommerce-api-legacy`

| ID | Severidade | Problema | Arquivo/Linhas | Impacto |
| -- | ---------- | -------- | -------------- | ------- |
| P2-C1 | CRITICAL | Credenciais hardcoded (DB, gateway, SMTP) | `src/utils.js:1-7` | Comprometimento de integrações se o código vazar |
| P2-C2 | CRITICAL | God Class `AppManager` (DB + rotas + checkout + relatório) | `src/AppManager.js:1-141` | Zero separação MVC; mudança em checkout afeta admin e users |
| P2-H1 | HIGH | Crypto custom inseguro (`badCrypto`) | `src/utils.js:17-23` | Senhas trivialmente reversíveis/colidem |
| P2-H2 | HIGH | Estado global mutável (`globalCache`, `totalRevenue`) | `src/utils.js:9-10` | Comportamento não determinístico entre requests |
| P2-M1 | MEDIUM | N+1 no relatório financeiro (cursos→matrículas→users→payments) | `src/AppManager.js:80-126` | Latência e race na montagem do JSON |
| P2-M2 | MEDIUM | Validação fraca + respostas `res.send(string)` misturadas com JSON | `src/AppManager.js:35-55` | Contratos inconsistentes; inputs malformados passam |
| P2-L1 | LOW | Nomenclatura opaca (`u`, `e`, `p`, `cc`) | `src/AppManager.js:29-33` | Legibilidade e onboarding ruins |
| P2-L2 | LOW | DELETE de usuário sem limpeza de FKs (mensagem admite dados sujos) | `src/AppManager.js:131-136` | Integridade referencial quebrada |

#### Detalhamento — Projeto 2

**P2-C1.** Objeto `config` embute `dbPass`, `paymentGatewayKey` e `smtpUser` no fonte (`utils.js:1-7`).

**P2-C2.** `AppManager` cria o banco, faz seed, registra checkout, relatório e delete (`AppManager.js:4-138`).

**P2-H1.** `badCrypto` concatena base64 em loop e corta 10 caracteres — não é hash criptográfico (`utils.js:17-23`).

**P2-H2.** Cache e contador mutáveis no módulo (`utils.js:9-10`), alterados por `logAndCache`.

**P2-M1.** Para cada curso, query de enrollments; para cada enrollment, user + payment (`AppManager.js:89-125`).

**P2-M2.** Checkout só testa truthiness; erros retornam texto puro (`res.send("Bad Request")`) enquanto sucesso usa `res.json`.

**P2-L1 / P2-L2.** Variáveis de uma letra; `DELETE` remove só `users` e responde admitindo órfãos.

**Evidências de stack:** Node.js + Express 4.18 + sqlite3; SQLite `:memory:`; domínio LMS (courses, enrollments, payments, checkout); God Class em `src/`.

---

### Projeto 3 — `task-manager-api`

| ID | Severidade | Problema | Arquivo/Linhas | Impacto |
| -- | ---------- | -------- | -------------- | ------- |
| P3-C1 | CRITICAL | Hash de senha com MD5 | `models/user.py:27-32` | Senhas quebráveis por rainbow table |
| P3-H1 | HIGH | `to_dict()` serializa o hash da senha | `models/user.py:16-25` | Vazamento de credenciais em GET/POST de usuários |
| P3-H2 | HIGH | Lógica de negócio e serialização pesada nas rotas | `routes/task_routes.py:11-63`, `85-154` | Rotas inchadas; MVC apenas nominal |
| P3-H3 | HIGH | Token JWT fake no login | `routes/user_routes.py:207-210` | Autenticação ilusória; qualquer cliente forja token |
| P3-M1 | MEDIUM | Credenciais SMTP hardcoded no service | `services/notification_service.py:7-10` | Segredo de e-mail no repositório |
| P3-M2 | MEDIUM | Lógica `is_overdue` duplicada em múltiplos handlers | `task_routes.py:30-39`, `71-80`; `user_routes.py:171-180`; `report_routes.py:33-43` | Drift de regra de atraso |
| P3-L1 | LOW | `type(tags) == list` em vez de `isinstance` | `routes/task_routes.py:141` | Estilo frágil; falha com subclasses |
| P3-L2 | LOW | `datetime.utcnow()` deprecated (Python 3.12+) | `models/*.py`, `routes/*.py`, `seed.py` | Warnings e futura remoção da API |

#### Detalhamento — Projeto 3

**P3-C1.** `set_password` / `check_password` usam `hashlib.md5` sem salt (`user.py:29-32`).

**P3-H1.** O dicionário de serialização inclui `'password': self.password` (`user.py:21`), usado em create/update/login/get.

**P3-H2.** `GET /tasks` monta dict manual, calcula overdue e faz N+1 de user/category; `POST /tasks` concentra validação + persistência na rota.

**P3-H3.** Resposta de login devolve um token previsível do tipo `fake-jwt-token-<id>` (`user_routes.py:210`).

> O valor original presente no código legado foi redigido neste relatório por segurança. O finding foi identificado antes da refatoração.

**P3-M1.** `email_user` / `email_password` fixos na classe (`notification_service.py:9-10`).

**P3-M2.** O model já tem `is_overdue()` (`task.py:50-60`), mas as rotas reimplementam a mesma árvore de `if`s.

**P3-L1 / P3-L2.** Comparação de tipo com `type(...) == list`; uso disseminado de `datetime.utcnow()`.

**Evidências de stack:** Python + Flask 3.0 + Flask-SQLAlchemy + marshmallow (declarado, pouco usado nas rotas); SQLite `tasks.db`; domínio Task Manager; arquitetura em camadas parciais (`models/`, `routes/`, `services/`, `utils/`) sem controllers dedicados nem config externa.

---

## Construção da Skill

### Decisões arquiteturais

A Skill vive em `code-smells-project/.claude/skills/refactor-arch/` e foi **copiada byte a byte** para os outros dois projetos. Isso prova portabilidade: o mesmo pacote de conhecimento serve Flask cru, Express e Flask+SQLAlchemy.

Estrutura adotada (alinhada ao enunciado):

```text
refactor-arch/
├── SKILL.md                  # orquestrador das 3 fases (~150 linhas)
├── project-analysis.md       # heurísticas agnósticas de stack
├── anti-patterns.md          # 12 anti-patterns + deprecated APIs
├── audit-report-template.md  # template do relatório
├── mvc-guidelines.md         # responsabilidades MVC para APIs
└── refactoring-playbook.md   # 10 padrões BEFORE/AFTER (Python + JS)
```

O `SKILL.md` é deliberadamente curto e aponta as referências sob demanda (progressive disclosure): o agente só carrega o catálogo na Fase 2 e o playbook na Fase 3.

### Por que esses anti-patterns

Os 12 itens do catálogo cobrem exatamente os problemas observados na análise manual:

1. God Class/Module — `models.py` e `AppManager`
2. Hardcoded secrets — os três projetos
3. SQL Injection — projeto 1
4. Business logic in routes — projetos 2 e 3
5. Tight coupling — conexão global / God Class
6. Global mutable state — `database.py`, `utils.js`
7. Duplicated code — validações e `is_overdue`
8. Missing validation — checkout e gaps pontuais
9. N+1 — pedidos, relatório financeiro, tasks
10. Magic numbers / naming — descontos e `u/e/p`
11. Inconsistent errors — `res.send` vs JSON; bare `except`
12. Deprecated APIs — MD5, `utcnow`, debug hardcoded, crypto caseiro

### Classificação de severidade

Segue a escala do desafio: CRITICAL = segurança/integridade ou God Class destrutiva; HIGH = violação grave de MVC/SOLID; MEDIUM = duplicação/N+1/validação; LOW = legibilidade/deprecated de baixo risco. O catálogo documenta quando elevar ou reduzir.

### Detecção de tecnologias (agnóstica)

`project-analysis.md` não procura “arquivos Flask”. A ordem é: manifesto (`requirements.txt` vs `package.json`) → imports → entry point → rotas → ORM/SQL → domínio por vocabulário. Flask e Express são *resultados* da detecção, não premissas.

### Human-in-the-loop

A Fase 2 termina com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e proibição explícita de alterar a aplicação antes do `y`. Isso evita refatoração cega e atende ao requisito acadêmico de supervisão humana.

### Estratégia de refatoração

O playbook ordena: inventário de contratos → config/secrets → estrutura MVC → SQL seguro → extrair lógica → erros/validação → estado global/deprecated → DRY → validação de boot/endpoints. No projeto 3, a guideline manda **não destruir** pastas já úteis — só introduzir controllers/config/middleware onde houver ganho.

### Dificuldades encontradas

- Distinguir “camadas parciais” (projeto 3) de “MVC adequado”: a Skill precisa melhorar sem reescrever por vaidade.
- Linhas exatas exigem leitura integral; heurísticas por grep sozinhas geram falsos positivos (ex.: SQL com `?` não é injection).
- Preservar contratos estranhos (`usr`/`eml`/`c_id` no checkout) durante a refatoração Express.

---

## Resultados

### Projeto 1 — `code-smells-project`

#### Antes

- Arquitetura: monólito plano (`app.py`, `controllers.py`, `models.py`, `database.py`)
- Findings: **13** (CRITICAL 4 · HIGH 3 · MEDIUM 3 · LOW 3)
- Relatório: [`reports/audit-project-1.md`](reports/audit-project-1.md)

#### Depois

- Arquitetura: MVC (`config/`, `models/`, `controllers/`, `views/`, `middlewares/`, `validators/`)
- Problemas eliminados: **12** (SQLi parametrizado, secrets via env, hash de senha, God Module, health sem secret, `flask.g`, N+1→JOIN, validator, error middleware, constantes, logging, debug via env)
- Problemas restantes: **1** — `POST /admin/query` ainda aceita SQL livre (endpoint preservado por contrato)
- Boot: **PASS** (`python app.py`, sem Traceback)
- Endpoints: **19/19** preservados
- Smoke: **21/21 PASS** + `POST /admin/reset-db` PASS
- Testes automatizados: nenhum existia no repositório (0/0)

### Projeto 2 — `ecommerce-api-legacy`

#### Antes

- Arquitetura: God Class `AppManager` + `utils.js` com secrets/cache/`badCrypto`
- Findings: **11** (CRITICAL 3 · HIGH 3 · MEDIUM 3 · LOW 2)
- Cobertura manual: 8/8
- Relatório: [`reports/audit-project-2.md`](reports/audit-project-2.md)

#### Depois

- Arquitetura: MVC Express (`config/`, `models/`, `services/`, `controllers/`, `routes/`, `middlewares/`, `validators/`, `utils/crypto.js`)
- Problemas eliminados: **10** fixed + **1** parcialmente (DELETE ainda usa `res.send` textual; erros viraram JSON)
- Boot: **PASS**
- Endpoints: **3/3** preservados (paths/métodos/body de sucesso do checkout)
- Smoke: **8/8 PASS**
- Testes automatizados: nenhum existia (0/0)
- **Skill portability: PASS** — hashes dos 6 arquivos de `refactor-arch` idênticos aos do Projeto 1; a mesma Skill detectou stack Node/Express por heurísticas (`package.json` + `express` + `sqlite3`) sem regras específicas para `AppManager.js`

### Projeto 3 — `task-manager-api`

#### Antes

- Arquitetura: camadas parciais (`models/`, `routes/`, `services/`, `utils/`) — Routes POOR
- Findings: **12** (CRITICAL 3 · HIGH 4 · MEDIUM 3 · LOW 2)
- Cobertura manual: 8/8 (100%)
- Relatório: [`reports/audit-project-3.md`](reports/audit-project-3.md)

#### Depois

- Arquitetura: MVC incremental (`config/`, `controllers/`, `middlewares/`, `validators/` + pastas preservadas)
- Problemas eliminados: **12/12**
- Boot: **PASS**
- Endpoints: **22/22**
- Smoke: **26/26 PASS**
- Testes automatizados: nenhum existia (0/0)
- Security greps: MD5/utcnow/query.get/fake-jwt/secrets ausentes

### Tabela comparativa dos três projetos

| Projeto | Stack | Findings | Corrigidos | Restantes | Endpoints | Boot | Validação |
| ------- | ----- | -------: | ---------: | --------: | --------: | ---- | --------- |
| code-smells-project | Python/Flask + sqlite3 | 13 | 12 | 1 (`/admin/query`) | 19/19 | PASS | Smoke 21/21 |
| ecommerce-api-legacy | Node/Express + sqlite3 | 11 | 10 | 1 parcial (DELETE `send`) | 3/3 | PASS | Smoke 8/8 |
| task-manager-api | Python/Flask + SQLAlchemy | 12 | 12 | 0 | 22/22 | PASS | Smoke 26/26 |

### Evidência de portabilidade da Skill

- A pasta `.claude/skills/refactor-arch/` (6 arquivos) foi **copiada byte a byte** nos 3 projetos; hashes idênticos **antes** das execuções.
- Projeto 1: Python/Flask + SQLite/`sqlite3` cru  
- Projeto 2: JavaScript/Express + SQLite  
- Projeto 3: Python/Flask + SQLAlchemy ORM + organização parcial  
- Nenhum finding ou heurística hardcoded por nome de arquivo de domínio (`AppManager`, `Task`, etc.).
- Isso demonstra que a Skill é **agnóstica de tecnologia**: detecta stack por manifestos/imports e aplica o mesmo catálogo MVC/anti-patterns.


---

## Checklist de Validação

### Projeto 1 — code-smells-project

#### Fase 1

- [x] Linguagem detectada
- [x] Framework detectado
- [x] Domínio detectado
- [x] Arquivos contabilizados

#### Fase 2

- [x] >= 5 findings
- [x] >= 1 CRITICAL/HIGH
- [x] arquivo e linhas exatas
- [x] ordenação por severidade
- [x] deprecated APIs analisadas
- [x] confirmação humana solicitada

#### Fase 3

- [x] MVC aplicado
- [x] config separada
- [x] models separados
- [x] routes/views separadas
- [x] controllers separados
- [x] error handling centralizado
- [x] aplicação inicia
- [x] endpoints funcionam

### Projeto 2 — ecommerce-api-legacy

#### Fase 1

- [x] Linguagem detectada
- [x] Framework detectado
- [x] Domínio detectado
- [x] Arquivos contabilizados

#### Fase 2

- [x] >= 5 findings
- [x] >= 1 CRITICAL/HIGH
- [x] arquivo e linhas exatas
- [x] ordenação por severidade
- [x] deprecated APIs analisadas
- [x] confirmação humana solicitada

#### Fase 3

- [x] MVC aplicado
- [x] config separada
- [x] models separados
- [x] routes/views separadas
- [x] controllers separados
- [x] error handling centralizado
- [x] aplicação inicia
- [x] endpoints funcionam

### Projeto 3 — task-manager-api

#### Fase 1

- [x] Linguagem detectada
- [x] Framework detectado
- [x] Domínio detectado
- [x] Arquivos contabilizados

#### Fase 2

- [x] >= 5 findings
- [x] >= 1 CRITICAL/HIGH
- [x] arquivo e linhas exatas
- [x] ordenação por severidade
- [x] deprecated APIs analisadas
- [x] confirmação humana solicitada

#### Fase 3

- [x] MVC aplicado
- [x] config separada
- [x] models separados
- [x] routes/views separadas
- [x] controllers separados
- [x] error handling centralizado
- [x] aplicação inicia
- [x] endpoints funcionam

---

## Como Executar

### Pré-requisitos

- Claude Code instalado e autenticado (para invocar a Skill)
- Python 3.10+ (projetos 1 e 3)
- Node.js 18+ e npm (projeto 2)
- Git (opcional)

Defaults locais (`dev-only-change-me`, `dev-payment-key`) são **placeholders de desenvolvimento**. Em qualquer ambiente real, defina variáveis de ambiente (`SECRET_KEY`, `PAYMENT_GATEWAY_KEY`, etc.).

### Instalação das dependências

```bash
# Projeto 1
cd code-smells-project
pip install -r requirements.txt

# Projeto 2
cd ../ecommerce-api-legacy
npm install

# Projeto 3
cd ../task-manager-api
pip install -r requirements.txt
python seed.py   # seed com senhas de demonstração acadêmica apenas
```

### Execução das aplicações

```bash
# Projeto 1 — http://localhost:5000
cd code-smells-project && python app.py

# Projeto 2 — http://localhost:3000
cd ecommerce-api-legacy && npm start

# Projeto 3 — http://localhost:5000
cd task-manager-api && python app.py
```

### Smoke tests (reproduzíveis)

Os scripts usam banco temporário / porta efêmera e **não deixam processos pendurados**. São **smoke tests** (não testes unitários automatizados de suíte).

```bash
# Projeto 1 — esperado: 21 passed / 0 failed
cd code-smells-project
python scripts/smoke_test.py

# Projeto 2 — esperado: 8 passed / 0 failed
cd ../ecommerce-api-legacy
node scripts/smoke_test.js

# Projeto 3 — esperado: 26 passed / 0 failed
cd ../task-manager-api
python scripts/smoke_test.py
```

### Execução da Skill

```bash
cd code-smells-project
claude "/refactor-arch"
# Após Phase 2: responda y somente se concordar com o relatório

cd ../ecommerce-api-legacy
claude "/refactor-arch"

cd ../task-manager-api
claude "/refactor-arch"
```

A Skill genérica sugere `reports/audit.md` (ou `reports/audit-<project-name>.md`). Nesta entrega MBA os relatórios foram nomeados `reports/audit-project-{1,2,3}.md` por convenção acadêmica.

---

## Evidências de Execução

A evidência desta entrega é **textual e reproduzível** (logs de boot + saída dos smoke tests + comandos acima). Não dependemos de screenshots.

| Projeto | Smoke script | Resultado reexecutado |
| ------- | ------------ | --------------------- |
| code-smells-project | `python scripts/smoke_test.py` | **21 passed / 0 failed** |
| ecommerce-api-legacy | `node scripts/smoke_test.js` | **8 passed / 0 failed** |
| task-manager-api | `python scripts/smoke_test.py` | **26 passed / 0 failed** |

Automated unit tests: **0** em todos os projetos (não existiam no boilerplate).

### Incidentes reais de ambiente (não são falhas finais)

- **Projeto 1:** boot inicial falhou por `.env` com encoding inválido no ambiente do usuário; contornado com `load_dotenv=False` / leitura segura do `.env` do projeto. Boot subsequente e smoke PASS.
- **Projeto 2:** porta 3000 ocupada por outro processo Node; liberada e reiniciada. Boot e smoke PASS.

### Skill portability

- 6/6 arquivos de `refactor-arch` idênticos nos três projetos (hashes recalculados após ajustes de acabamento).
- Stacks: Flask+sqlite3 · Express+sqlite3 · Flask+SQLAlchemy.
- Sem findings hardcoded por nome de projeto.

---

## Limitações e Dívidas Residuais

### Projeto 1 — `POST /admin/query`

Endpoint legado **preservado** para manter o contrato dos 19 endpoints. Continua permitindo SQL arbitrário (risco conhecido). Em produção: remover, exigir autenticação forte e allowlist, ou substituir por operações de domínio tipadas. **Não foi removido** porque a regra de entrega exige preservação de contratos.

### Projeto 2 — `DELETE /api/users/:id`

Erros da API foram padronizados em JSON `{ error }`. O **sucesso do DELETE** permanece textual (`res.send(...)`) por compatibilidade com o contrato legado documentado. Cascade de enrollments/payments foi aplicado (integridade).

### Projeto 3 — dependências ociosas

`marshmallow` (e parcialmente o potencial de `requests`) permanece em `requirements.txt` sem uso nas rotas refatoradas — **technical debt LOW**. Remoção exigiria alteração de manifesto além do escopo mínimo da Phase 3; validators próprios cobrem a validação atual.

### Seeds / defaults

Senhas de seed (`admin123`, `1234`, etc.) e defaults `dev-*` são **somente demonstração local**, nunca credenciais de ambiente real.

---
