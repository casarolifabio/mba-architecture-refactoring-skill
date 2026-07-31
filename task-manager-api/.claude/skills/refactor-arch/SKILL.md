---
name: refactor-arch
description: >-
  Audita e refatora projetos legados para MVC em 3 fases (análise, auditoria com
  confirmação humana, refatoração). Agnóstica de tecnologia — detecta Python/Flask,
  Node/Express e outras stacks. Use quando o usuário invocar /refactor-arch ou
  pedir auditoria/refatoração arquitetural MVC.
disable-model-invocation: true
---

# refactor-arch — Auditoria e Refatoração Arquitetural

Skill agnóstica de tecnologia. Executa **exatamente três fases** em sequência.
**NÃO modifique nenhum arquivo da aplicação nas Fases 1 e 2.**

## Referências (carregar sob demanda)

| Fase | Arquivo | Quando ler |
|------|---------|------------|
| 1 | [project-analysis.md](project-analysis.md) | Antes de detectar stack |
| 2 | [anti-patterns.md](anti-patterns.md) | Antes de auditar |
| 2 | [audit-report-template.md](audit-report-template.md) | Ao gerar o relatório |
| 3 | [mvc-guidelines.md](mvc-guidelines.md) | Antes de refatorar |
| 3 | [refactoring-playbook.md](refactoring-playbook.md) | Durante a refatoração |

---

## PHASE 1 — PROJECT ANALYSIS

Leia `project-analysis.md` e aplique as heurísticas ao projeto atual (cwd).

### O que detectar

1. Linguagem (manifestos + imports + extensões)
2. Framework web
3. Package manager e dependências principais
4. Banco de dados / ORM / query layer
5. Domínio provável (nomes de rotas, models, seeds)
6. Arquitetura atual (monólito plano, God Class, camadas parciais, MVC)
7. Entry point
8. Arquivos de código relevantes (excluir `node_modules`, `venv`, `.git`, `__pycache__`)
9. Rotas/endpoints (método + path)
10. Models/entities, controllers/services, config, middlewares, testes

### Saída obrigatória

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:
Framework:
Dependencies:
Database:
Domain:
Architecture:
Source files:
Endpoints:
================================
```

Preencha cada campo com evidência real. Não invente. Em seguida avance para a Fase 2 **sem modificar código**.

---

## PHASE 2 — ARCHITECTURE AUDIT

1. Leia `anti-patterns.md` por completo.
2. Analise **todo** o código relevante do projeto.
3. Para cada anti-pattern do catálogo, procure os sinais de detecção.
4. Se o sinal **não existir**, **não reporte** o finding.
5. Inclua detecção de **APIs deprecated** (obrigatório — ver seção no catálogo).
6. Cada finding deve ter linhas **exatas** lidas do arquivo (não invente números).

### Formato de cada finding

```text
[SEVERITY] Nome

File: caminho:linhaInicial-linhaFinal
Description:
Evidence:
Impact:
Recommendation:
```

### Ordenação

CRITICAL → HIGH → MEDIUM → LOW

### Resumo obrigatório

```text
CRITICAL: X
HIGH: X
MEDIUM: X
LOW: X

Total: X findings
```

### Relatório

Leia `audit-report-template.md` e grave o relatório em:

- `reports/audit.md` (preferencial, agnóstico), ou
- `reports/audit-<project-name>.md` se houver múltiplos projetos no monorepo.

> **Nota de entrega acadêmica:** nomes como `audit-project-1.md` são convenção desta entrega MBA, não regra da Skill.

### Confirmação humana — OBRIGATÓRIA

Ao terminar a Fase 2:

1. **PARE.**
2. **NÃO** modifique nenhum arquivo da aplicação.
3. Mostre exatamente:

```text
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

4. Aguarde resposta explícita `y` / `yes` / `sim`. Qualquer outra resposta → não refatore.

---

## PHASE 3 — REFACTORING

Somente após confirmação explícita.

1. Leia `mvc-guidelines.md` e `refactoring-playbook.md`.
2. Inventarie endpoints existentes (método, path, params, body, status, formato).
3. Refatore para MVC adequado à stack detectada:

| Camada API REST | Responsabilidade |
|-----------------|------------------|
| View / Routes | HTTP: declarar endpoint, extrair input, serializar response |
| Controller | Coordenar caso de uso, chamar model/service, controlar fluxo |
| Model | Domínio + persistência (sem conhecer HTTP) |
| Config | Env, secrets, conexão |
| Middleware | Auth, logging, erros, validações transversais |
| Services | Lógica de negócio reutilizável (somente se fizer sentido) |
| Entry point | Composition root |

### Regras da Fase 3

- Preserve contratos públicos (paths, métodos, formatos de resposta).
- Não remova funcionalidades para “simplificar”.
- Se o projeto já tiver camadas razoáveis, refatore de forma **incremental** — não destrua organização boa.
- Extraia secrets para config/env.
- Centralize error handling.
- Substitua APIs deprecated.
- Use parâmetros bindados em queries (fim de SQL injection).

### Validação

1. Instalar dependências se necessário.
2. Subir a aplicação.
3. Testar endpoints inventariados.
4. Executar testes automatizados se existirem.
5. Registrar evidências reais (comandos + resultados).
6. Nunca afirmar que passou sem ter executado.

### Saída final

```text
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
(árvore)

## Validation
  ✓/✗ Application boots
  ✓/✗ Endpoints respond
  ✓/✗ Tests (se houver)
================================
```

---

## Regras globais

- Agnóstica: descubra a stack primeiro; adapte sinais e estrutura alvo.
- Não force findings falsos.
- Não invente linhas de código.
- Human-in-the-loop entre Fase 2 e Fase 3 é obrigatório.
- Não faça commit/push a menos que o usuário peça.
