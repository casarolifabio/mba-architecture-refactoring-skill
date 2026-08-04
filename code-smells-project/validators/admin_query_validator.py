"""Validação de SQL somente-leitura para POST /admin/query (PB-3)."""
from __future__ import annotations

import re

from validators.produto_validator import ValidationError

# Tabelas do schema local — allowlist explícita
ALLOWED_TABLES = frozenset(
    {
        "produtos",
        "usuarios",
        "pedidos",
        "itens_pedido",
        "sqlite_master",
    }
)

_FORBIDDEN = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REINDEX",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "INTO",  # SELECT INTO / INSERT INTO
)


def validate_readonly_select(query: str) -> str:
    """
    Aceita apenas um único SELECT somente-leitura contra tabelas allowlisted.
    Rejeita multi-statement, comentários e DML/DDL.
    """
    if not query or not isinstance(query, str):
        raise ValidationError("Query não informada")

    sql = query.strip()
    if not sql:
        raise ValidationError("Query não informada")

    if ";" in sql.rstrip(";"):
        raise ValidationError("Multi-statement SQL não permitido")

    sql = sql.rstrip(";").strip()
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise ValidationError("Comentários SQL não permitidos")

    upper = sql.upper()
    if not upper.startswith("SELECT"):
        raise ValidationError("Apenas SELECT é permitido neste endpoint")

    for kw in _FORBIDDEN:
        if re.search(rf"\b{kw}\b", upper):
            raise ValidationError(f"Palavra-chave não permitida: {kw}")

    tables = re.findall(
        r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)",
        sql,
        flags=re.IGNORECASE,
    )
    if not tables:
        raise ValidationError("SELECT deve referenciar tabela(s) explícita(s)")

    for table in tables:
        if table.lower() not in ALLOWED_TABLES:
            raise ValidationError(f"Tabela não permitida: {table}")

    return sql
