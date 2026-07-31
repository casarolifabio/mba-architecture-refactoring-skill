# Architecture Audit Report

## Project Information

Project:
Language:
Framework:
Database:
Architecture:
Files analyzed:
Lines analyzed:

## Executive Summary

CRITICAL:
HIGH:
MEDIUM:
LOW:
TOTAL:

## Findings

### [CRITICAL] <Nome>

**File:** <caminho>
**Lines:** <inicio>-<fim>
**Evidence:** <trecho ou descrição factual do código>
**Description:** <o que está errado>
**Impact:** <risco concreto>
**Recommendation:** <como corrigir>

### [HIGH] <Nome>

**File:**
**Lines:**
**Evidence:**
**Description:**
**Impact:**
**Recommendation:**

### [MEDIUM] <Nome>

**File:**
**Lines:**
**Evidence:**
**Description:**
**Impact:**
**Recommendation:**

### [LOW] <Nome>

**File:**
**Lines:**
**Evidence:**
**Description:**
**Impact:**
**Recommendation:**

## Architecture Assessment

<Descrever o nível atual (monólito / God Class / camadas parciais), principais acoplamentos e riscos.>

## Recommended Target Architecture

```text
<árvore MVC proposta adequada à stack>
```

## Validation Plan

1. Inventário de endpoints (método, path, contrato)
2. Instalação de dependências
3. Boot da aplicação
4. Smoke test dos endpoints
5. Execução de testes automatizados (se existirem)
6. Comparação antes/depois dos contratos públicos

## Deprecated APIs Reviewed

| API | Local | Severidade | Ação |
|-----|-------|------------|------|
| | | | |

---

**Ordenação:** findings devem aparecer CRITICAL → HIGH → MEDIUM → LOW.
**Regra:** não inventar findings; linhas devem ser exatas.
