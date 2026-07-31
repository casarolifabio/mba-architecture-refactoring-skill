# ecommerce-api-legacy

LMS API (checkout) em Node.js/Express — refatorada para MVC (`refactor-arch` Phase 3).

## Como rodar

```bash
npm install
npm start
```

Variáveis de ambiente opcionais: `PORT`, `DB_PATH`, `PAYMENT_GATEWAY_KEY`, `SMTP_USER`, `DB_USER`, `DB_PASS`.  
Default `PAYMENT_GATEWAY_KEY=dev-payment-key` é **placeholder de desenvolvimento**.

A aplicação sobe em `http://localhost:3000`. O banco SQLite padrão é `:memory:` e carrega seeds no boot.

Exemplos de requisições em `api.http`.

## Smoke tests

```bash
node scripts/smoke_test.js
```

Esperado: **8 passed / 0 failed** (sobe porta efêmera e encerra o processo).
