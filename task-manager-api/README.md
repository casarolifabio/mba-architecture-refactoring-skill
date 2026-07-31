# task-manager-api

API de Task Manager em Python/Flask — refatorada incrementalmente para MVC (`refactor-arch` Phase 3).

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

Variáveis: ver `.env.example` (`SECRET_KEY`, `DEBUG`, `SQLALCHEMY_DATABASE_URI`, SMTP_*).  
Default `SECRET_KEY=dev-only-change-me` é **placeholder de desenvolvimento**. Senhas do `seed.py` são **somente demonstração acadêmica**.

A aplicação sobe em `http://localhost:5000`.

## Smoke tests

```bash
python scripts/smoke_test.py
```

Esperado: **26 passed / 0 failed**.
