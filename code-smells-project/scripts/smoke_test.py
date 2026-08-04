"""
Smoke tests reproduzíveis — code-smells-project (Flask test client).
Uso: python scripts/smoke_test.py
Exit 0 = todos PASS; exit 1 = falha.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Banco temporário — não altera loja.db local
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE"] = _tmp.name
os.environ["SECRET_KEY"] = "smoke-test-secret"
os.environ["DEBUG"] = "false"

from app import create_app  # noqa: E402

app = create_app()
client = app.test_client()

passed = 0
failed = 0
results: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        results.append(f"PASS {name}")
    else:
        failed += 1
        results.append(f"FAIL {name} {detail}")


def main() -> int:
    r = client.get("/")
    check("GET /", r.status_code == 200)

    r = client.get("/health")
    j = r.get_json()
    check(
        "GET /health",
        r.status_code == 200 and j.get("status") == "ok" and "secret_key" not in j,
        str(j),
    )

    r = client.get("/produtos")
    j = r.get_json()
    check("GET /produtos", r.status_code == 200 and j.get("sucesso") is True)

    r = client.get("/produtos/busca", query_string={"q": "Mouse"})
    check("GET /produtos/busca", r.status_code == 200 and r.get_json().get("sucesso") is True)

    r = client.get("/produtos/1")
    check("GET /produtos/1", r.status_code == 200)

    r = client.post(
        "/produtos",
        json={
            "nome": "Cabo USB",
            "preco": 19.9,
            "estoque": 5,
            "categoria": "informatica",
        },
    )
    j = r.get_json()
    new_id = j.get("dados", {}).get("id") if isinstance(j, dict) else None
    check("POST /produtos", r.status_code == 201 and new_id)

    if new_id:
        r = client.put(
            f"/produtos/{new_id}",
            json={
                "nome": "Cabo USB-C",
                "preco": 24.9,
                "estoque": 5,
                "categoria": "informatica",
            },
        )
        check("PUT /produtos/<id>", r.status_code == 200)

    r = client.get("/usuarios")
    j = r.get_json()
    users = j.get("dados") if isinstance(j, dict) else None
    no_senha = isinstance(users, list) and all("senha" not in u for u in users)
    check("GET /usuarios", r.status_code == 200 and no_senha)

    r = client.get("/usuarios/1")
    j = r.get_json()
    check(
        "GET /usuarios/1",
        r.status_code == 200 and "senha" not in (j.get("dados") or {}),
    )

    r = client.post(
        "/usuarios",
        json={"nome": "Ana", "email": "ana-smoke@test.com", "senha": "teste123"},
    )
    check("POST /usuarios", r.status_code == 201)

    r = client.post("/login", json={"email": "joao@email.com", "senha": "123456"})
    check("POST /login ok", r.status_code == 200 and r.get_json().get("sucesso") is True)

    r = client.post("/login", json={"email": "joao@email.com", "senha": "errada"})
    check("POST /login fail", r.status_code == 401)

    r = client.post(
        "/pedidos",
        json={"usuario_id": 2, "itens": [{"produto_id": 2, "quantidade": 1}]},
    )
    j = r.get_json()
    pedido_id = j.get("dados", {}).get("pedido_id") if isinstance(j, dict) else None
    check("POST /pedidos", r.status_code == 201 and pedido_id)

    r = client.get("/pedidos")
    check("GET /pedidos", r.status_code == 200)

    r = client.get("/pedidos/usuario/2")
    check("GET /pedidos/usuario/<id>", r.status_code == 200)

    if pedido_id:
        r = client.put(f"/pedidos/{pedido_id}/status", json={"status": "aprovado"})
        check("PUT /pedidos/<id>/status", r.status_code == 200)

    r = client.get("/relatorios/vendas")
    check("GET /relatorios/vendas", r.status_code == 200)

    # POST /admin/query — PB-3: auth + allowlist (não é mais SQL livre)
    r = client.post("/admin/query", json={"sql": "SELECT COUNT(*) AS c FROM produtos"})
    check("POST /admin/query sem auth 401", r.status_code == 401)

    r = client.post(
        "/admin/query",
        json={
            "email": "joao@email.com",
            "senha": "123456",
            "sql": "SELECT COUNT(*) AS c FROM produtos",
        },
    )
    check("POST /admin/query cliente 403", r.status_code == 403)

    r = client.post(
        "/admin/query",
        json={
            "email": "admin@loja.com",
            "senha": "admin123",
            "sql": "SELECT COUNT(*) AS c FROM produtos",
        },
    )
    check(
        "POST /admin/query admin SELECT 200",
        r.status_code == 200 and r.get_json().get("sucesso") is True,
        str(r.get_json()),
    )

    r = client.post(
        "/admin/query",
        json={
            "email": "admin@loja.com",
            "senha": "admin123",
            "sql": "DROP TABLE produtos",
        },
    )
    check("POST /admin/query DROP rejeitado", r.status_code == 400)

    if new_id:
        r = client.delete(f"/produtos/{new_id}")
        check("DELETE /produtos/<id>", r.status_code == 200)

    r = client.get("/produtos/99999")
    check("GET /produtos/99999 404", r.status_code == 404)

    r = client.get("/produtos/busca", query_string={"q": "' OR '1'='1"})
    check("GET /produtos/busca injection-safe", r.status_code == 200)

    print("==== SMOKE code-smells-project ====")
    for line in results:
        print(line)
    print(f"PASSED={passed} FAILED={failed} TOTAL={passed + failed}")

    try:
        os.unlink(_tmp.name)
    except OSError:
        pass

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
