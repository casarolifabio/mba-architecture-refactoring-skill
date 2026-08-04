# code-smells-project

API de E-commerce em Python/Flask refatorada para MVC (`refactor-arch` Phase 3).

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

Variáveis de ambiente opcionais: `SECRET_KEY`, `DEBUG`, `DATABASE`, `HOST`, `PORT`.  
Default `SECRET_KEY=dev-only-change-me` é **placeholder de desenvolvimento** — defina em produção.

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, com produtos e usuários de exemplo (senhas com hash; **somente demonstração acadêmica**).

## Smoke tests

```bash
python scripts/smoke_test.py
```

Esperado: **24 passed / 0 failed**.
