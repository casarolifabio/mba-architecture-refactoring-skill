"""
Smoke tests reproduzíveis — task-manager-api (Flask test client).
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

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{_tmp.name}"
os.environ["SECRET_KEY"] = "smoke-test-secret"
os.environ["DEBUG"] = "false"
os.environ["SMTP_ENABLED"] = "false"

from app import app  # noqa: E402  — env já definido
from seed import seed_data  # noqa: E402

seed_data()
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


def no_password(payload) -> bool:
    if isinstance(payload, dict):
        if "password" in payload:
            return False
        user = payload.get("user")
        if isinstance(user, dict) and "password" in user:
            return False
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and "password" in item:
                return False
    return True


def main() -> int:
    r = client.get("/")
    check("GET /", r.status_code == 200)

    r = client.get("/health")
    check("GET /health", r.status_code == 200)

    r = client.get("/users")
    check("GET /users", r.status_code == 200 and no_password(r.get_json()))

    r = client.get("/users/1")
    check("GET /users/1", r.status_code == 200 and no_password(r.get_json()))

    r = client.post(
        "/users",
        json={"name": "Teste", "email": "teste-smoke@x.com", "password": "abcd"},
    )
    check("POST /users", r.status_code == 201 and no_password(r.get_json()))

    r = client.put("/users/2", json={"name": "Maria Atualizada"})
    check("PUT /users/2", r.status_code == 200 and no_password(r.get_json()))

    r = client.post("/login", json={"email": "joao@email.com", "password": "1234"})
    j = r.get_json()
    check(
        "POST /login ok",
        r.status_code == 200
        and j.get("token")
        and not str(j.get("token", "")).startswith("fake-jwt")
        and no_password(j),
        str(j)[:120],
    )

    r = client.post("/login", json={"email": "joao@email.com", "password": "wrong"})
    check("POST /login fail", r.status_code == 401)

    r = client.get("/users/1/tasks")
    check("GET /users/1/tasks", r.status_code == 200)

    r = client.get("/tasks")
    check("GET /tasks", r.status_code == 200)

    r = client.get("/tasks/1")
    check("GET /tasks/1", r.status_code == 200)

    r = client.post(
        "/tasks",
        json={
            "title": "Nova task smoke",
            "priority": 2,
            "user_id": 1,
            "category_id": 1,
        },
    )
    j = r.get_json()
    tid = j.get("id") if isinstance(j, dict) else None
    check("POST /tasks", r.status_code == 201 and tid)

    if tid:
        r = client.put(f"/tasks/{tid}", json={"status": "in_progress"})
        check("PUT /tasks/<id>", r.status_code == 200)

    r = client.get("/tasks/search", query_string={"q": "auth"})
    check("GET /tasks/search", r.status_code == 200)

    r = client.get("/tasks/stats")
    check("GET /tasks/stats", r.status_code == 200)

    if tid:
        r = client.delete(f"/tasks/{tid}")
        check("DELETE /tasks/<id>", r.status_code == 200)

    r = client.get("/categories")
    check("GET /categories", r.status_code == 200)

    r = client.post("/categories", json={"name": "QA"})
    j = r.get_json()
    cid = j.get("id") if isinstance(j, dict) else None
    check("POST /categories", r.status_code == 201 and cid)

    if cid:
        r = client.put(f"/categories/{cid}", json={"description": "qualidade"})
        check("PUT /categories/<id>", r.status_code == 200)

    r = client.get("/reports/summary")
    check("GET /reports/summary", r.status_code == 200)

    r = client.get("/reports/user/1")
    check("GET /reports/user/1", r.status_code == 200)

    if cid:
        r = client.delete(f"/categories/{cid}")
        check("DELETE /categories/<id>", r.status_code == 200)

    r = client.post("/tasks", json={"title": "ab"})
    check("POST /tasks invalid 400", r.status_code == 400)

    r = client.get("/tasks/99999")
    check("GET /tasks/99999 404", r.status_code == 404)

    r = client.get("/users")
    users = r.get_json()
    check("GET /users again", r.status_code == 200)
    deleted = False
    if isinstance(users, list):
        for u in users:
            if u.get("email") == "teste-smoke@x.com":
                r = client.delete(f"/users/{u['id']}")
                check("DELETE /users smoke", r.status_code == 200)
                deleted = True
                break
    if not deleted:
        check("DELETE /users smoke", False, "user not found")

    print("==== SMOKE task-manager-api ====")
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
