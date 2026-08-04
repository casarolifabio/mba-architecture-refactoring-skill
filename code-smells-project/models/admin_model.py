"""Consultas administrativas somente-leitura (SQL já validado)."""
from database import get_db


def execute_readonly_select(sql: str):
    """Executa SELECT allowlisted. `sql` deve vir de validate_readonly_select."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
